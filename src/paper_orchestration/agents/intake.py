"""Framework-executed intake agent."""

from __future__ import annotations

from typing import Any

from pydantic_ai import RunContext

from ..parsing import (
    clean_item_phrase,
    extract_requested_line_items,
    is_firm_order_request,
    parse_requested_delivery_date,
    resolve_item_name,
)
from ..schemas import ParsedRequest
from .base import AgentToolRecorder, make_framework_agent


class IntakeResult(ParsedRequest):
    notes: str = ""


class IntakeAgent(AgentToolRecorder):
    """Framework-executed agent that turns raw customer text into structured order intent."""

    def __init__(self) -> None:
        super().__init__("IntakeAgent")
        self.framework_agent = make_framework_agent(
            self.agent_name,
            "Extract delivery date, firm-order intent, quantities, and catalog-resolved item names "
            "from the customer request.",
            IntakeResult,
        )
        self._register_tools()

    def _register_tools(self) -> None:
        @self.framework_agent.tool
        def parse_delivery_date(ctx: RunContext, request_text: str, request_date: str) -> str:
            self.record_tool("parse_delivery_date", f"request_date={request_date}")
            return parse_requested_delivery_date(request_text, request_date)

        @self.framework_agent.tool
        def extract_line_items(ctx: RunContext, request_text: str) -> list[dict[str, Any]]:
            self.record_tool("extract_line_items", "raw customer request parsed")
            return [item.model_dump() for item in extract_requested_line_items(request_text)]

        @self.framework_agent.tool
        def classify_firm_order(ctx: RunContext, request_text: str) -> bool:
            self.record_tool("classify_firm_order", "customer intent classified")
            return is_firm_order_request(request_text)

        @self.framework_agent.tool
        def resolve_catalog_item(ctx: RunContext, raw_item: str) -> str | None:
            self.record_tool("resolve_catalog_item", f"raw_item={raw_item}")
            return resolve_item_name(clean_item_phrase(raw_item))

    def run_intake(self, request_text: str, request_date: str) -> IntakeResult:
        prompt = f"""
Customer request date: {request_date}
Customer request text:
{request_text}

Use the tools to parse delivery date, firm-order intent, and line items. Return an IntakeResult.
Each item must preserve the raw phrase and include the catalog item_name when a catalog match
exists.
""".strip()
        return self._output(self.framework_agent.run_sync(prompt))
