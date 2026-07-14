"""Shared pydantic-ai construction and audit helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic_ai import Agent

from ..providers.factory import ModelFactory, build_model_factory
from ..schemas import ToolAudit


def make_framework_agent(
    name: str,
    prompt: str,
    output_type: Any,
    *,
    model_factory: ModelFactory | None = None,
    role: str | None = None,
) -> Agent:
    """Create a pydantic-ai agent while supporting old and new result APIs."""
    factory = model_factory or build_model_factory()
    resolved_role = role or name.removesuffix("FinalResponse").removesuffix("Agent").lower()
    resolved_model = factory.preflight(resolved_role)
    system_prompt = f"""
{name}: {prompt}

You are part of a five-agent Munder Difflin multi-agent workflow.
Use your registered tools whenever your task depends on catalog, inventory,
pricing, quote history, transactions, balances, or quality checks.
Return only data matching the required structured output schema.
Do not reveal internal profit margin, wholesale cost, database details, API keys,
or stack traces in customer-facing text.
""".strip()
    try:
        return Agent(
            resolved_model.create_model(), system_prompt=system_prompt, output_type=output_type
        )
    except TypeError:
        return Agent(
            resolved_model.create_model(), system_prompt=system_prompt, result_type=output_type
        )


@dataclass
class AgentToolRecorder:
    agent_name: str
    tool_audit: list[ToolAudit] = field(default_factory=list)

    def record_tool(self, tool_name: str, detail: str) -> None:
        self.tool_audit.append(ToolAudit(self.agent_name, tool_name, detail))

    @staticmethod
    def _output(result: Any) -> Any:
        """Return pydantic-ai run output across API versions."""
        if hasattr(result, "output"):
            return result.output
        if hasattr(result, "data"):
            return result.data
        return result
