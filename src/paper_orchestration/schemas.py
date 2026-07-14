"""Pydantic contracts shared by package components."""

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
