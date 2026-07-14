"""Provider contracts used before constructing pydantic-ai agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ModelCapabilities:
    """Capabilities required by the workflow's model boundary."""

    structured_output: bool
    tool_calling: bool
    structured_output_emulated: bool = False
    tool_calling_emulated: bool = False

    def missing_required(self) -> tuple[str, ...]:
        missing: list[str] = []
        if not (self.structured_output or self.structured_output_emulated):
            missing.append("structured_output")
        if not (self.tool_calling or self.tool_calling_emulated):
            missing.append("tool_calling")
        return tuple(missing)


def capabilities_from_names(names: frozenset[str]) -> ModelCapabilities:
    """Translate secret-free TOML capability names into the typed contract."""
    return ModelCapabilities(
        structured_output="structured_output" in names,
        tool_calling="tool_calling" in names,
        structured_output_emulated="structured_output_emulated" in names,
        tool_calling_emulated="tool_calling_emulated" in names,
    )


class ProviderAdapter(Protocol):
    """Adapter contract for creating a pydantic-ai model safely."""

    provider: str
    model: str

    def capabilities(self) -> ModelCapabilities:
        """Return native or validated emulated model capabilities."""

    def create_model(self) -> Any:
        """Return the model value accepted by pydantic-ai Agent."""


class ModelCompatibilityError(RuntimeError):
    """Raised when a configured model cannot satisfy a workflow role."""

    def __init__(self, provider: str, model: str, role: str, missing: tuple[str, ...]) -> None:
        self.provider = provider
        self.model = model
        self.role = role
        self.missing = missing
        capabilities = ", ".join(missing)
        super().__init__(
            f"Model compatibility preflight failed for provider {provider!r}, model {model!r}, "
            f"role {role!r}: missing required capabilities: {capabilities}."
        )
