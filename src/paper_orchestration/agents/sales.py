# ruff: noqa: E501
"""Framework-executed sales agent."""

from __future__ import annotations

from typing import Any

from pydantic_ai import RunContext

from ..database import (
    create_transaction,
    generate_financial_report,
    get_cash_balance,
    get_connection,
)
from ..parsing import canonical_item_name
from ..pricing import get_wholesale_cost
from ..schemas import SalesDecision, TransactionPlanLine
from .base import AgentToolRecorder, make_framework_agent
from .intake import IntakeResult
from .inventory import InventoryResult
from .quoting import QuoteResult


class SalesResult(SalesDecision):
    cash_after: float
    inventory_after: float
    notes: str = ""


class SalesAgent(AgentToolRecorder):
    """Framework-executed agent that records only fully fulfillable firm orders."""

    def __init__(self) -> None:
        super().__init__("SalesAgent")
        self.framework_agent = make_framework_agent(
            self.agent_name,
            "Finalize only fully fulfillable firm orders, record idempotent transactions, and report financial state.",
            SalesResult,
        )
        self.pending_request_date = ""
        self.pending_transaction_plan: list[TransactionPlanLine] = []
        self.pending_commit_result: SalesResult | None = None
        self._register_tools()

    def _transaction_exists(
        self,
        item_name: str,
        transaction_type: str,
        quantity: int,
        price: float,
        date: str,
    ) -> int | None:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT rowid FROM transactions
                WHERE item_name IS ?
                  AND transaction_type = ?
                  AND units = ?
                  AND ABS(price - ?) < 0.0001
                  AND transaction_date = ?
                LIMIT 1
                """,
                (item_name, transaction_type, quantity, price, date),
            ).fetchone()
        return int(row[0]) if row else None

    @staticmethod
    def build_transaction_plan(
        parsed: IntakeResult,
        inventory: InventoryResult,
        quote: QuoteResult,
    ) -> list[TransactionPlanLine]:
        plan: list[TransactionPlanLine] = []

        for assessment in inventory.assessments:
            canonical_name = canonical_item_name(assessment.item_name)
            if canonical_name and assessment.reorder_needed and assessment.missing_quantity > 0:
                plan.append(
                    TransactionPlanLine(
                        item_name=canonical_name,
                        transaction_type="stock_orders",
                        quantity=assessment.missing_quantity,
                        price=get_wholesale_cost(
                            canonical_name,
                            assessment.missing_quantity,
                        ),
                        transaction_date=parsed.request_date,
                    )
                )

        for line in quote.lines:
            canonical_name = canonical_item_name(line.item_name)
            if canonical_name is None:
                continue
            plan.append(
                TransactionPlanLine(
                    item_name=canonical_name,
                    transaction_type="sales",
                    quantity=line.quantity,
                    price=line.line_total,
                    transaction_date=parsed.request_date,
                )
            )

        return plan

    @staticmethod
    def summarize_transaction_plan(plan: list[TransactionPlanLine]) -> dict[str, float]:
        gross_sales = round(
            sum(
                transaction.price for transaction in plan if transaction.transaction_type == "sales"
            ),
            2,
        )
        restock_spend = round(
            sum(
                transaction.price
                for transaction in plan
                if transaction.transaction_type == "stock_orders"
            ),
            2,
        )
        return {
            "gross_sales": gross_sales,
            "restock_spend": restock_spend,
            "expected_net_cash_delta": round(gross_sales - restock_spend, 2),
        }

    def commit_transaction_plan(self) -> SalesResult:
        if self.pending_commit_result is not None:
            return self.pending_commit_result

        transaction_ids: list[int] = []

        for transaction in self.pending_transaction_plan:
            transaction_ids.append(
                create_transaction(
                    transaction.item_name,
                    transaction.transaction_type,
                    transaction.quantity,
                    transaction.price,
                    transaction.transaction_date,
                )
            )

        report = generate_financial_report(self.pending_request_date)
        summary = self.summarize_transaction_plan(self.pending_transaction_plan)

        result = SalesResult(
            sale_recorded=bool(transaction_ids),
            transaction_ids=transaction_ids,
            reason="Validated transaction plan committed.",
            cash_after=report["cash_balance"],
            inventory_after=report["inventory_value"],
            notes=(
                f"gross_sales=${summary['gross_sales']:.2f}; "
                f"restock_spend=${summary['restock_spend']:.2f}; "
                f"expected_net_cash_delta=${summary['expected_net_cash_delta']:.2f}"
            ),
        )

        self.pending_commit_result = result
        return result

    def _register_tools(self) -> None:
        @self.framework_agent.tool
        def commit_validated_transaction_plan(ctx: RunContext) -> dict[str, Any]:
            self.record_tool(
                "commit_validated_transaction_plan",
                f"{len(self.pending_transaction_plan)} deterministic transactions",
            )
            return self.commit_transaction_plan().model_dump()

        @self.framework_agent.tool
        def cash_balance(ctx: RunContext, as_of_date: str) -> float:
            self.record_tool("cash_balance", f"as_of_date={as_of_date}")
            return get_cash_balance(as_of_date)

        @self.framework_agent.tool
        def financial_report(ctx: RunContext, as_of_date: str) -> dict[str, Any]:
            self.record_tool("financial_report", f"as_of_date={as_of_date}")
            return generate_financial_report(as_of_date)

    def run_sales(
        self, parsed: IntakeResult, inventory: InventoryResult, quote: QuoteResult
    ) -> SalesResult:
        self.pending_request_date = parsed.request_date
        self.pending_transaction_plan = self.build_transaction_plan(parsed, inventory, quote)
        self.pending_commit_result = None
        summary = self.summarize_transaction_plan(self.pending_transaction_plan)
        prompt = f"""
Parsed request JSON:
{parsed.model_dump_json(indent=2)}

Inventory result JSON:
{inventory.model_dump_json(indent=2)}

Quote result JSON:
{quote.model_dump_json(indent=2)}

Validated transaction plan JSON:
{[transaction.model_dump() for transaction in self.pending_transaction_plan]}

Validated transaction summary:
{summary}

The Orchestrator has already confirmed this is a firm, fully fulfillable order.
Review the validated transaction plan for consistency.
Call commit_validated_transaction_plan exactly once.
Return the SalesResult from that tool without inventing, removing, or changing transaction rows.
""".strip()
        review = self._output(self.framework_agent.run_sync(prompt))

        if self.pending_commit_result is None:
            self.record_tool(
                "commit_validated_transaction_plan",
                f"{len(self.pending_transaction_plan)} deterministic transactions committed by fallback",
            )
            committed = self.commit_transaction_plan()
        else:
            committed = self.pending_commit_result

        if isinstance(review, SalesResult) and review.notes:
            committed.notes = f"{committed.notes}; model_review={review.notes}"

        return committed
