# ruff: noqa: E501
"""Framework-executed inventory agent."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic_ai import RunContext

from ..database import get_all_inventory, get_stock_level, get_supplier_delivery_date
from ..parsing import canonical_item_name
from ..schemas import InventoryAssessment
from .base import AgentToolRecorder, make_framework_agent
from .intake import IntakeResult


class InventoryResult(BaseModel):
    assessments: list[InventoryAssessment]
    notes: str = ""


class InventoryAgent(AgentToolRecorder):
    """Framework-executed agent that checks stock and reorder feasibility."""

    def __init__(self) -> None:
        super().__init__("InventoryAgent")
        self.framework_agent = make_framework_agent(
            self.agent_name,
            "Check stock, reorder needs, and supplier delivery dates. Do not quote prices or record sales.",
            InventoryResult,
        )
        self._register_tools()

    def _register_tools(self) -> None:
        @self.framework_agent.tool
        def inventory_snapshot(ctx: RunContext, as_of_date: str) -> dict[str, int]:
            self.record_tool("inventory_snapshot", f"as_of_date={as_of_date}")
            return get_all_inventory(as_of_date)

        @self.framework_agent.tool
        def item_stock_level(ctx: RunContext, item_name: str, as_of_date: str) -> dict[str, Any]:
            canonical_name = canonical_item_name(item_name)
            self.record_tool(
                "item_stock_level",
                f"item_name={item_name} -> {canonical_name or 'unmatched'}, as_of_date={as_of_date}",
            )
            if canonical_name is None:
                return {"item_name": item_name, "current_stock": 0}
            stock_df = get_stock_level(canonical_name, as_of_date)
            return (
                stock_df.to_dict(orient="records")[0]
                if not stock_df.empty
                else {"item_name": canonical_name, "current_stock": 0}
            )

        @self.framework_agent.tool
        def supplier_delivery_eta(ctx: RunContext, request_date: str, quantity: int) -> str:
            self.record_tool(
                "supplier_delivery_eta", f"request_date={request_date}, quantity={quantity}"
            )
            return get_supplier_delivery_date(request_date, quantity)

    def run_inventory(self, parsed: IntakeResult) -> InventoryResult:
        prompt = f"""
Parsed request JSON:
{parsed.model_dump_json(indent=2)}

Use inventory_snapshot at least once for the request date. For each requested item:
- If item_name is null, mark can_fulfill false with reason "not carried in the current catalog".
- Otherwise use item_stock_level for the exact item and request date.
- If stock is short, use supplier_delivery_eta for the missing quantity.
- Mark reorder_needed true only when supplier ETA is on or before requested_delivery_date.
Return InventoryResult with one InventoryAssessment per requested item.
""".strip()
        return self._output(self.framework_agent.run_sync(prompt))
