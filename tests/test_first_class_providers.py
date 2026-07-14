from pathlib import Path

import pytest

from paper_orchestration.config import ProviderProfile, Settings
from paper_orchestration.providers.base import ModelCapabilities
from paper_orchestration.providers.factory import ModelFactory
from paper_orchestration.providers.first_class import (
    ProviderConfigurationError,
    build_first_class_adapter,
)


def profile(provider: str, model: str) -> ProviderProfile:
    return ProviderProfile(name=provider, provider=provider, model=model)


@pytest.mark.parametrize(
    ("provider", "model", "env_name"),
    [
        ("openai", "gpt-test", "OPENAI_API_KEY"),
        ("anthropic", "claude-test", "ANTHROPIC_API_KEY"),
        ("gemini", "gemini-test", "GEMINI_API_KEY"),
    ],
)
def test_hosted_adapters_construct_without_network_access(provider, model, env_name, monkeypatch):
    monkeypatch.setenv(env_name, "fake-key")

    adapter = build_first_class_adapter(provider, model, profile(provider, model))

    assert isinstance(adapter.create_model(), object)
    assert adapter.capabilities() == ModelCapabilities(structured_output=True, tool_calling=True)


def test_ollama_adapter_constructs_from_local_endpoint(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    adapter = build_first_class_adapter(
        "ollama",
        "gpt-oss:20b",
        ProviderProfile(
            name="ollama",
            provider="ollama",
            model="gpt-oss:20b",
            base_url="http://127.0.0.1:11434/v1",
        ),
    )

    assert adapter.create_model() is not None


def test_missing_provider_secret_is_provider_specific(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ProviderConfigurationError, match="Anthropic.*ANTHROPIC_API_KEY"):
        build_first_class_adapter("anthropic", "claude-test", profile("anthropic", "claude-test"))


def test_invalid_ollama_endpoint_is_provider_specific():
    with pytest.raises(ProviderConfigurationError, match="Ollama.*absolute HTTP"):
        build_first_class_adapter(
            "ollama",
            "local-test",
            ProviderProfile(name="ollama", provider="ollama", model="local-test", base_url="local"),
        )


def test_factory_constructs_first_class_adapter_for_role(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
    settings = Settings(
        api_key="fake-key",
        model="openai:gpt-test",
        database_path=Path("outputs/test.db"),
        profile_name="openai",
        provider="openai",
        profiles={"openai": profile("openai", "gpt-test")},
    )

    resolved = ModelFactory(settings).preflight("intake")

    assert resolved.provider == "openai"
    assert resolved.adapter.capabilities().missing_required() == ()
