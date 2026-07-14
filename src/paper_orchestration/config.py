"""Runtime configuration for the refactored package."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    model: str
    database_path: Path
    ollama_base_url: str | None = None


def load_settings() -> Settings:
    """Load live-agent settings without requiring configuration at import time."""
    load_dotenv()
    model = os.getenv(
        "PAPER_ORCHESTRATION_MODEL",
        os.getenv(
            "OPENAI_MODEL",
            os.getenv("BEAVERS_CHOICE_AGENT_MODEL", "openai:gpt-4o-mini"),
        ),
    )
    provider = model.partition(":")[0]
    api_key = os.getenv("OPENAI_API_KEY")
    ollama_base_url = None

    if provider == "ollama":
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
        os.environ.setdefault("OLLAMA_BASE_URL", ollama_base_url)
        api_key = None
    elif not api_key:
        raise RuntimeError(
            "Set OPENAI_API_KEY in .env or the environment before running the project."
        )

    return Settings(
        api_key=api_key,
        model=model,
        database_path=Path(os.getenv("BEAVERS_CHOICE_DB_PATH", "outputs/munder_difflin.db")),
        ollama_base_url=ollama_base_url,
    )
