import json
import os
from urllib.error import URLError
from urllib.request import urlopen

import pytest

from paper_orchestration.agents.intake import IntakeAgent, IntakeResult

DEFAULT_OLLAMA_API_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "gpt-oss:20b"


def _available_ollama_models(api_url: str) -> set[str]:
    try:
        with urlopen(f"{api_url}/api/tags", timeout=3) as response:  # noqa: S310
            payload = json.load(response)
    except (OSError, URLError):
        return set()

    return {model["name"] for model in payload.get("models", [])}


@pytest.mark.ollama
def test_local_ollama_executes_tools_and_returns_structured_output(monkeypatch) -> None:
    api_url = os.getenv("OLLAMA_TEST_API_URL", DEFAULT_OLLAMA_API_URL).rstrip("/")
    model_name = os.getenv("OLLAMA_TEST_MODEL", DEFAULT_OLLAMA_MODEL)
    available_models = _available_ollama_models(api_url)
    if model_name not in available_models:
        pytest.skip(f"Ollama model {model_name!r} is not available at {api_url}")

    monkeypatch.setenv("PAPER_ORCHESTRATION_MODEL", f"ollama:{model_name}")
    monkeypatch.setenv("OLLAMA_BASE_URL", f"{api_url}/v1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    agent = IntakeAgent()
    result = agent.run_intake(
        "Please quote 100 sheets of A4 paper for delivery January 10, 2025.",
        "2025-01-01",
    )

    assert isinstance(result, IntakeResult)
    assert result.requested_delivery_date == "2025-01-10"
    assert result.items
    assert any(audit.tool_name == "parse_delivery_date" for audit in agent.tool_audit)

