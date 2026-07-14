import warnings
from pathlib import Path

import pytest

from paper_orchestration.config import load_settings


def test_ollama_model_does_not_require_openai_credentials(monkeypatch) -> None:
    monkeypatch.setenv("PAPER_ORCHESTRATION_MODEL", "ollama:gpt-oss:20b")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    settings = load_settings()

    assert settings.model == "ollama:gpt-oss:20b"
    assert settings.api_key is None
    assert settings.ollama_base_url == "http://127.0.0.1:11434/v1"


def test_openai_model_still_requires_openai_credentials(monkeypatch) -> None:
    monkeypatch.setenv("PAPER_ORCHESTRATION_MODEL", "openai:gpt-4o-mini")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        load_settings()


def test_existing_openai_configuration_still_loads(monkeypatch) -> None:
    monkeypatch.delenv("PAPER_ORCHESTRATION_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "openai:gpt-4o-mini")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    settings = load_settings()

    assert settings.model == "openai:gpt-4o-mini"
    assert settings.api_key == "test-key"
    assert settings.ollama_base_url is None


def test_toml_profiles_and_agent_overrides_are_typed(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "models.toml"
    config.write_text(
        """version = 1
default_profile = \"gemini\"

[profiles.openai]
provider = \"openai\"
model = \"gpt-4o-mini\"
api_key_env = \"OPENAI_API_KEY\"

[profiles.anthropic]
provider = \"anthropic\"
model = \"claude-test\"
api_key_env = \"ANTHROPIC_API_KEY\"

[profiles.gemini]
provider = \"gemini\"
model = \"gemini-test\"
api_key_env = \"GEMINI_API_KEY\"

[profiles.ollama]
provider = \"ollama\"
model = \"local-test\"
base_url = \"http://localhost:11434/v1\"

[agents.quoting]
profile = \"anthropic\"
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.delenv("PAPER_ORCHESTRATION_MODEL", raising=False)
    monkeypatch.delenv("PAPER_ORCHESTRATION_PROFILE", raising=False)

    settings = load_settings(config)

    assert settings.profile_name == "gemini"
    assert settings.model == "gemini:gemini-test"
    assert settings.agent_overrides["quoting"].profile == "anthropic"
    assert settings.resolve_agent_model("quoting") == "anthropic:claude-test"
    assert set(settings.profiles) == {"openai", "anthropic", "gemini", "ollama"}


def test_legacy_only_configuration_warns_and_preserves_model(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "openai:gpt-4o-mini")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("PAPER_ORCHESTRATION_CONFIG", "missing-model-providers.toml")

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        settings = load_settings()

    assert settings.model == "openai:gpt-4o-mini"
    assert any("deprecated" in str(item.message) for item in captured)


def test_missing_profile_secret_does_not_expose_secret_value(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "models.toml"
    config.write_text(
        """version = 1
default_profile = "openai"
[profiles.openai]
provider = "openai"
model = "test"
api_key_env = "OPENAI_API_KEY"
""",
        encoding="utf-8",
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="Profile 'openai'.*OPENAI_API_KEY"):
        load_settings(config)
