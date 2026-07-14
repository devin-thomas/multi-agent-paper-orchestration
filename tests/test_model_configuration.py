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
