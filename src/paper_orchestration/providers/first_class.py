"""First-class Pydantic AI provider adapters."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider

from ..config import ProviderProfile
from .base import ModelCapabilities, capabilities_from_names


class ProviderConfigurationError(RuntimeError):
    """Raised when a first-class provider cannot be constructed safely."""


@dataclass(frozen=True)
class FirstClassProviderAdapter:
    """Construct one provider-specific Pydantic AI model from a secret-free profile."""

    provider: str
    model: str
    profile: ProviderProfile

    _capabilities: ModelCapabilities

    def capabilities(self) -> ModelCapabilities:
        return self._capabilities

    def create_model(self):
        if self.provider == "openai":
            return OpenAIChatModel(self.model, provider=OpenAIProvider(**self._client_options()))
        if self.provider == "anthropic":
            return AnthropicModel(self.model, provider=AnthropicProvider(**self._client_options()))
        if self.provider == "gemini":
            return GoogleModel(self.model, provider=GoogleProvider(**self._client_options()))
        if self.provider == "ollama":
            options = self._client_options()
            return OpenAIChatModel(
                self.model,
                provider=OpenAIProvider(
                    base_url=options["base_url"], api_key=options.get("api_key", "ollama")
                ),
            )
        raise ProviderConfigurationError(f"Unsupported provider {self.provider!r}")

    def _client_options(self) -> dict[str, str]:
        if self.provider == "ollama":
            base_url = self.profile.base_url or os.getenv(
                "OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"
            )
            _validate_url(self.provider, base_url)
            return {"base_url": base_url}

        api_key_env = self.profile.api_key_env or {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
        }[self.provider]
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ProviderConfigurationError(
                f"{self.provider.title()} profile requires the {api_key_env} environment variable."
            )
        options = {"api_key": api_key}
        base_url = self.profile.base_url or (
            os.getenv(self.profile.base_url_env) if self.profile.base_url_env else None
        )
        if base_url:
            _validate_url(self.provider, base_url)
            options["base_url"] = base_url
        return options


def _validate_url(provider: str, value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ProviderConfigurationError(
            f"{provider.title()} provider base URL must be an absolute HTTP(S) URL."
        )


def build_first_class_adapter(
    provider: str, model: str, profile: ProviderProfile
) -> FirstClassProviderAdapter:
    """Build a supported adapter while keeping provider details out of agents."""
    if provider not in {"openai", "anthropic", "gemini", "ollama"}:
        raise ProviderConfigurationError(f"Unsupported provider {provider!r}")
    adapter = FirstClassProviderAdapter(
        provider=provider,
        model=model,
        profile=profile,
        _capabilities=capabilities_from_names(profile.capabilities),
    )
    adapter._client_options()
    return adapter
