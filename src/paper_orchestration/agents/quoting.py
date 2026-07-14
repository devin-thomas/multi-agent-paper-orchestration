# ruff: noqa: E501
"""Framework-executed quoting agent."""

from __future__ import annotations

from typing import Any

from pydantic_ai import RunContext

from ..database import search_quote_history
from ..parsing import canonical_item_name
from ..pricing import calculate_discount, get_unit_price
from ..providers.factory import ModelFactory
from ..schemas import QuoteProposal
from .base import AgentToolRecorder, make_framework_agent
from .intake import IntakeResult
from .inventory import InventoryResult


class QuoteResult(QuoteProposal):
    notes: str = ""


class QuotingAgent(AgentToolRecorder):
    """Framework-executed agent that generates quote lines and rationale."""

    def __init__(self, model_factory: ModelFactory | None = None) -> None:
        super().__init__("QuotingAgent")
        self.framework_agent = make_framework_agent(
            self.agent_name,
            "Generate explainable quotes using catalog prices, volume discounts, and historical quote context. Do not mutate inventory.",
            QuoteResult,
            model_factory=model_factory,
            role="quoting",
        )
        self._register_tools()

    def _register_tools(self) -> None:
        @self.framework_agent.tool
        def quote_history_search(
            ctx: RunContext, search_terms: list[str], limit: int = 5
        ) -> list[dict[str, Any]]:
            self.record_tool("quote_history_search", f"terms={search_terms}, limit={limit}")
            return search_quote_history(search_terms, limit)

        @self.framework_agent.tool
        def catalog_unit_price(ctx: RunContext, item_name: str) -> float:
            canonical_name = canonical_item_name(item_name)
            self.record_tool(
                "catalog_unit_price", f"item_name={item_name} -> {canonical_name or 'unmatched'}"
            )
            return get_unit_price(canonical_name) if canonical_name else 0.0

        @self.framework_agent.tool
        def volume_discount(ctx: RunContext, quantity: int, need_size: str) -> float:
            self.record_tool("volume_discount", f"quantity={quantity}, need_size={need_size}")
            return calculate_discount(quantity, need_size.lower())

    def run_quote(
        self, parsed: IntakeResult, inventory: InventoryResult, request_context: dict[str, Any]
    ) -> QuoteResult:
        prompt = f"""
Parsed request JSON:
{parsed.model_dump_json(indent=2)}

Inventory result JSON:
{inventory.model_dump_json(indent=2)}

Request context JSON:
{request_context}

Use quote_history_search once with job, event, and need_size terms when available.
For each inventory assessment that can be fulfilled and has an item_name:
- Use catalog_unit_price with the exact item_name from the Inventory result; do not rewrite punctuation or parentheses.
- Use volume_discount with the item quantity and need_size.
- Compute quoted_unit_price = list_unit_price * (1 - discount_rate).
- Compute line_total = quoted_unit_price * quantity.
- Use the requested delivery date unless an item has a reorder_delivery_date.
Return QuoteResult. Do not include unfulfillable items as quote lines.
""".strip()
        return self._output(self.framework_agent.run_sync(prompt))
