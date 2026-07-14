"""Provider-neutral runtime configuration without agent imports."""

from __future__ import annotations

import os
import re
import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib

from dotenv import load_dotenv

SUPPORTED_PROVIDERS = frozenset({"openai", "anthropic", "gemini", "ollama"})
PROVIDER_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
DEFAULT_CONFIG_PATH = Path("model-providers.toml")


@dataclass(frozen=True)
class ProviderProfile:
    """A validated, secret-free provider profile loaded from TOML."""

    name: str
    provider: str
    model: str
    api_key_env: str | None = None
    base_url: str | None = None
    base_url_env: str | None = None
    capabilities: frozenset[str] = frozenset({"structured_output", "tool_calling"})


@dataclass(frozen=True)
class AgentModelOverride:
    profile: str | None = None
    model: str | None = None


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    model: str
    database_path: Path
    ollama_base_url: str | None = None
    profile_name: str = ""
    provider: str = ""
    base_url: str | None = None
    profiles: Mapping[str, ProviderProfile] | None = None
    agent_overrides: Mapping[str, AgentModelOverride] | None = None

    def resolve_agent_model(self, role: str) -> str:
        """Apply role override, then global profile/model selection."""
        profiles = self.profiles or {}
        override = (self.agent_overrides or {}).get(role)
        selected = profiles.get(override.profile) if override and override.profile else None
        provider = selected.provider if selected else self.provider
        model = (
            override.model
            if override and override.model
            else selected.model
            if selected
            else self.model
        )
        if ":" in model:
            prefix, _, model_name = model.partition(":")
            if prefix in SUPPORTED_PROVIDERS:
                provider, model = prefix, model_name
        elif model.startswith(f"{provider}:"):
            model = model[len(provider) + 1 :]
        return f"{provider}:{model}"


def _configuration_error(message: str) -> ValueError:
    return ValueError(f"Invalid model configuration: {message}")


def _read_config(
    path: Path,
) -> tuple[str, dict[str, ProviderProfile], dict[str, AgentModelOverride]]:
    if not path.exists():
        return "", {}, {}
    try:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise _configuration_error(f"could not read {path}: {exc}") from exc

    if raw.get("version") != 1:
        raise _configuration_error(f"{path} must declare version = 1")
    default_profile = raw.get("default_profile")
    if not isinstance(default_profile, str) or not default_profile:
        raise _configuration_error(f"{path} must define a non-empty default_profile")
    raw_profiles = raw.get("profiles")
    if not isinstance(raw_profiles, dict) or not raw_profiles:
        raise _configuration_error("at least one [profiles.<name>] table is required")

    profiles: dict[str, ProviderProfile] = {}
    for name, values in raw_profiles.items():
        if not isinstance(name, str) or not isinstance(values, dict):
            raise _configuration_error(f"profile {name!r} must be a TOML table")
        provider = values.get("provider")
        model = values.get("model")
        if not isinstance(provider, str) or not PROVIDER_NAME_PATTERN.fullmatch(provider):
            raise _configuration_error(
                f"profile {name!r} has invalid provider {provider!r}; use a provider extension name"
            )
        if not isinstance(model, str) or not model:
            raise _configuration_error(f"profile {name!r} requires a non-empty model")
        for field in ("api_key_env", "base_url", "base_url_env"):
            value = values.get(field)
            if value is not None and (not isinstance(value, str) or not value):
                raise _configuration_error(f"profile {name!r} has an invalid {field}")
        raw_capabilities = values.get("capabilities", ["structured_output", "tool_calling"])
        if not isinstance(raw_capabilities, list) or not all(
            isinstance(capability, str) and capability for capability in raw_capabilities
        ):
            raise _configuration_error(f"profile {name!r} has invalid capabilities")
        profiles[name] = ProviderProfile(
            name=name,
            provider=provider,
            model=model,
            api_key_env=values.get("api_key_env"),
            base_url=values.get("base_url"),
            base_url_env=values.get("base_url_env"),
            capabilities=frozenset(raw_capabilities),
        )
    if default_profile not in profiles:
        raise _configuration_error(f"default profile {default_profile!r} is not defined")

    overrides: dict[str, AgentModelOverride] = {}
    raw_agents = raw.get("agents", {})
    if not isinstance(raw_agents, dict):
        raise _configuration_error("[agents] must contain agent-role tables")
    for role, values in raw_agents.items():
        if not isinstance(values, dict):
            raise _configuration_error(f"agent override {role!r} must be a TOML table")
        profile = values.get("profile")
        model = values.get("model")
        if profile is not None and profile not in profiles:
            raise _configuration_error(
                f"agent override {role!r} references unknown profile {profile!r}"
            )
        if model is not None and (not isinstance(model, str) or not model):
            raise _configuration_error(f"agent override {role!r} has an invalid model")
        if profile is None and model is None:
            raise _configuration_error(f"agent override {role!r} must set profile or model")
        overrides[role] = AgentModelOverride(profile=profile, model=model)
    return default_profile, profiles, overrides


def load_settings(config_path: str | Path | None = None) -> Settings:
    """Load provider settings without requiring configuration at import time."""
    load_dotenv()
    env = os.environ
    path = Path(config_path or env.get("PAPER_ORCHESTRATION_CONFIG", DEFAULT_CONFIG_PATH))
    default_profile, profiles, overrides = _read_config(path)
    legacy_model = env.get("OPENAI_MODEL") or env.get("BEAVERS_CHOICE_AGENT_MODEL")
    explicit_model = env.get("PAPER_ORCHESTRATION_MODEL")
    selected_name = env.get("PAPER_ORCHESTRATION_PROFILE") or default_profile
    used_legacy = (
        not explicit_model
        and not env.get("PAPER_ORCHESTRATION_PROFILE")
        and bool(legacy_model)
    )

    if used_legacy:
        selected_name = "legacy-openai"
        profiles = {
            **profiles,
            selected_name: ProviderProfile(
                name=selected_name, provider="openai", model=legacy_model or "gpt-4o-mini"
            ),
        }

    if not profiles:
        selected_name = "legacy-openai"
        profiles = {
            selected_name: ProviderProfile(
                name=selected_name, provider="openai", model=legacy_model or "gpt-4o-mini"
            )
        }
        if legacy_model:
            warnings.warn(
                "Legacy model environment variables are deprecated; use model-providers.toml",
                DeprecationWarning,
                stacklevel=2,
            )
    elif used_legacy:
        warnings.warn(
            "Legacy model environment variables are deprecated; use PAPER_ORCHESTRATION_PROFILE",
            DeprecationWarning,
            stacklevel=2,
        )
    if selected_name not in profiles:
        raise _configuration_error(f"selected profile {selected_name!r} is not defined")

    profile = profiles[selected_name]
    model = explicit_model or profile.model
    provider = profile.provider
    if ":" in model:
        prefix, _, model_name = model.partition(":")
        if prefix in SUPPORTED_PROVIDERS:
            provider, model = prefix, model_name
    if not model:
        raise _configuration_error(f"profile {profile.name!r} resolved to an empty model")

    api_key_env = profile.api_key_env or {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }.get(provider)
    api_key = env.get(api_key_env) if api_key_env else None
    if api_key_env and not api_key:
        raise RuntimeError(
            f"Profile {profile.name!r} requires the {api_key_env} environment variable."
        )

    base_url = profile.base_url or (env.get(profile.base_url_env) if profile.base_url_env else None)
    ollama_base_url = None
    if provider == "ollama":
        ollama_base_url = base_url or env.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
        os.environ.setdefault("OLLAMA_BASE_URL", ollama_base_url)
        api_key = None
    return Settings(
        api_key=api_key,
        model=f"{provider}:{model}",
        database_path=Path(env.get("BEAVERS_CHOICE_DB_PATH", "outputs/munder_difflin.db")),
        ollama_base_url=ollama_base_url,
        profile_name=profile.name,
        provider=provider,
        base_url=base_url,
        profiles=profiles,
        agent_overrides=overrides,
    )
