"""Runtime configuration for the refactored package."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    database_path: Path


def load_settings() -> Settings:
    """Load live-agent settings without requiring configuration at import time."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set OPENAI_API_KEY in .env or the environment before running the project."
        )
    return Settings(
        api_key=api_key,
        model=os.getenv(
            "OPENAI_MODEL",
            os.getenv("BEAVERS_CHOICE_AGENT_MODEL", "openai:gpt-4o-mini"),
        ),
        database_path=Path(os.getenv("BEAVERS_CHOICE_DB_PATH", "outputs/munder_difflin.db")),
    )
