"""Pydantic and dataclass contracts shared by package components."""

from dataclasses import dataclass

from pydantic import BaseModel, Field


class RequestedItem(BaseModel):
    quantity: int = Field(ge=1)
    raw_item: str
    item_name: str | None = None


class ParsedRequest(BaseModel):
    request_date: str
    requested_delivery_date: str
    firm_order: bool
    items: list[RequestedItem]


class InventoryAssessment(BaseModel):
    item_name: str | None
    raw_item: str
    quantity: int
    current_stock: int = 0
    missing_quantity: int = 0
    can_fulfill: bool = False
    reorder_needed: bool = False
    reorder_delivery_date: str | None = None
    reason: str


class QuoteLine(BaseModel):
    item_name: str
    quantity: int
    list_unit_price: float
    discount_rate: float
    quoted_unit_price: float
    line_total: float
    delivery_date: str
    rationale: str
    reorder_needed: bool = False


class QuoteProposal(BaseModel):
    lines: list[QuoteLine] = Field(default_factory=list)
    total: float = 0.0
    historical_context: str = ""


class SalesDecision(BaseModel):
    sale_recorded: bool
    transaction_ids: list[int] = Field(default_factory=list)
    reason: str


class TransactionPlanLine(BaseModel):
    item_name: str
    transaction_type: str
    quantity: int
    price: float
    transaction_date: str


class ResponseEvaluation(BaseModel):
    passed: bool
    findings: list[str] = Field(default_factory=list)


class WorkflowResult(BaseModel):
    request_id: int
    source_row: int
    request_date: str
    requested_delivery_date: str
    order_status: str
    response: str
    cash_before: float
    cash_after: float
    inventory_before: float
    inventory_after: float
    gross_sales: float = 0.0
    restock_spend: float = 0.0
    expected_net_cash_delta: float = 0.0
    actual_cash_delta: float = 0.0
    fulfilled_items: list[str] = Field(default_factory=list)
    unfulfilled_items: list[str] = Field(default_factory=list)
    agent_route: str
    tool_calls: list[str] = Field(default_factory=list)
    evaluation_passed: bool = False
    evaluation_findings: list[str] = Field(default_factory=list)

    @property
    def cash_changed(self) -> bool:
        return round(self.cash_before, 2) != round(self.cash_after, 2)


@dataclass
class ToolAudit:
    agent_name: str
    tool_name: str
    detail: str

    def format(self) -> str:
        return f"{self.agent_name}.{self.tool_name}: {self.detail}"
