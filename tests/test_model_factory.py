from dataclasses import dataclass
from pathlib import Path

import pytest
from pydantic_ai.models.openai import OpenAIChatModel

from paper_orchestration.config import AgentModelOverride, ProviderProfile, Settings
from paper_orchestration.providers.base import ModelCapabilities, ModelCompatibilityError
from paper_orchestration.providers.factory import ModelFactory


def make_settings(
    *,
    default_profile: str = "local",
    overrides: dict[str, AgentModelOverride] | None = None,
    capabilities: frozenset[str] = frozenset({"structured_output", "tool_calling"}),
) -> Settings:
    profile = ProviderProfile(
        name="local", provider="ollama", model="small-model", capabilities=capabilities
    )
    hosted = ProviderProfile(
        name="hosted", provider="openai", model="gpt-test", capabilities=capabilities
    )
    return Settings(
        api_key=None,
        model="ollama:small-model",
        database_path=Path("outputs/test.db"),
        profile_name=default_profile,
        provider="ollama",
        profiles={"local": profile, "hosted": hosted},
        agent_overrides=overrides or {},
    )


def test_factory_resolves_global_default_and_role_override(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
    settings = make_settings(
        overrides={"quoting": AgentModelOverride(profile="hosted", model="special-model")}
    )

    factory = ModelFactory(settings)

    assert isinstance(factory.preflight("intake").create_model(), OpenAIChatModel)
    assert factory.preflight("quoting").model == "special-model"


def test_team_preflight_reports_precise_missing_capability() -> None:
    settings = make_settings(capabilities=frozenset({"structured_output"}))

    with pytest.raises(
        ModelCompatibilityError, match="provider 'ollama'.*role 'sales'.*tool_calling"
    ):
        ModelFactory(settings).preflight("sales")


@dataclass(frozen=True)
class RecordingAdapter:
    provider: str = "fake"
    model: str = "fake-model"
    created: list[str] | None = None

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(structured_output=True, tool_calling=True)

    def create_model(self) -> str:
        if self.created is not None:
            self.created.append("created")
        return "fake-model"


def test_team_preflight_completes_before_adapter_model_creation() -> None:
    created: list[str] = []
    adapter = RecordingAdapter(created=created)
    factory = ModelFactory(
        make_settings(), adapters={role: adapter for role in ("intake", "sales")}
    )

    factory.preflight_team(("intake", "sales"))

    assert created == []
