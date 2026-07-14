"""Project-owned model resolution and capability preflight."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..config import Settings, load_settings
from .base import (
    ModelCapabilities,
    ModelCompatibilityError,
    ProviderAdapter,
    capabilities_from_names,
)


@dataclass(frozen=True)
class ResolvedModel:
    """A role-specific model with its validated provider capabilities."""

    role: str
    provider: str
    model: str
    adapter: ProviderAdapter

    def create_model(self) -> Any:
        return self.adapter.create_model()


@dataclass(frozen=True)
class ConfiguredProviderAdapter:
    """Default adapter for the pydantic-ai provider model-string boundary."""

    provider: str
    model: str
    _capabilities: ModelCapabilities

    def capabilities(self) -> ModelCapabilities:
        return self._capabilities

    def create_model(self) -> str:
        return f"{self.provider}:{self.model}"


class ModelFactory:
    """Resolve role overrides and preflight capabilities before Agent creation."""

    def __init__(
        self, settings: Settings, adapters: dict[str, ProviderAdapter] | None = None
    ) -> None:
        self.settings = settings
        self._adapters = adapters or {}

    def resolve(self, role: str) -> ResolvedModel:
        model_name = self.settings.resolve_agent_model(role)
        provider, _, model = model_name.partition(":")
        if not provider or not model:
            raise ValueError(f"Invalid resolved model for role {role!r}: {model_name!r}")
        adapter = self._adapters.get(role) or self._adapters.get(provider)
        if adapter is None:
            profile = self._profile_for_role(role, provider)
            adapter = ConfiguredProviderAdapter(
                provider=provider,
                model=model,
                _capabilities=capabilities_from_names(profile.capabilities),
            )
        return ResolvedModel(role=role, provider=provider, model=model, adapter=adapter)

    def preflight(self, role: str) -> ResolvedModel:
        resolved = self.resolve(role)
        missing = resolved.adapter.capabilities().missing_required()
        if missing:
            raise ModelCompatibilityError(resolved.provider, resolved.model, role, missing)
        return resolved

    def preflight_team(self, roles: tuple[str, ...]) -> tuple[ResolvedModel, ...]:
        """Validate every role before constructing any framework agent."""
        resolved = tuple(self.resolve(role) for role in roles)
        for model in resolved:
            missing = model.adapter.capabilities().missing_required()
            if missing:
                raise ModelCompatibilityError(model.provider, model.model, model.role, missing)
        return resolved

    def _profile_for_role(self, role: str, provider: str):
        profiles = self.settings.profiles or {}
        override = (self.settings.agent_overrides or {}).get(role)
        profile = profiles.get(override.profile) if override and override.profile else None
        if profile is None:
            profile = profiles.get(self.settings.profile_name)
        if profile is None or profile.provider != provider:
            profile = next(
                (candidate for candidate in profiles.values() if candidate.provider == provider),
                None,
            )
        if profile is None:
            raise ValueError(
                f"No configured profile found for provider {provider!r}, role {role!r}"
            )
        return profile


def build_model_factory(
    settings: Settings | None = None,
    adapters: dict[str, ProviderAdapter] | None = None,
) -> ModelFactory:
    """Build the shared factory lazily so importing agents remains side-effect free."""
    return ModelFactory(settings or load_settings(), adapters=adapters)
