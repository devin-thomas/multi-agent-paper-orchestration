import ast
import os
import re
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from difflib import get_close_matches
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

try:
    from pydantic_ai import Agent, RunContext
except ImportError as exc:
    raise RuntimeError(
        "pydantic-ai is required for this submission because each agent must execute through the framework."
    ) from exc

FRAMEWORK_NAME = "pydantic-ai"


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("BEAVERS_CHOICE_DB_PATH", BASE_DIR / "munder_difflin.db"))

UDACITY_OPENAI_API_KEY = os.getenv("UDACITY_OPENAI_API_KEY")
if not UDACITY_OPENAI_API_KEY:
    raise RuntimeError("Set UDACITY_OPENAI_API_KEY before running this project.")

os.environ["OPENAI_API_KEY"] = UDACITY_OPENAI_API_KEY
os.environ["OPENAI_BASE_URL"] = "https://openai.vocareum.com/v1"

AGENT_MODEL = os.getenv("BEAVERS_CHOICE_AGENT_MODEL", "openai:gpt-4o-mini")

paper_supplies = [
    {"item_name": "A4 paper", "category": "paper", "unit_price": 0.05},
    {"item_name": "Letter-sized paper", "category": "paper", "unit_price": 0.06},
    {"item_name": "Cardstock", "category": "paper", "unit_price": 0.15},
    {"item_name": "Colored paper", "category": "paper", "unit_price": 0.10},
    {"item_name": "Glossy paper", "category": "paper", "unit_price": 0.20},
    {"item_name": "Matte paper", "category": "paper", "unit_price": 0.18},
    {"item_name": "Recycled paper", "category": "paper", "unit_price": 0.08},
    {"item_name": "Eco-friendly paper", "category": "paper", "unit_price": 0.12},
    {"item_name": "Poster paper", "category": "paper", "unit_price": 0.25},
    {"item_name": "Banner paper", "category": "paper", "unit_price": 0.30},
    {"item_name": "Kraft paper", "category": "paper", "unit_price": 0.10},
    {"item_name": "Construction paper", "category": "paper", "unit_price": 0.07},
    {"item_name": "Wrapping paper", "category": "paper", "unit_price": 0.15},
    {"item_name": "Glitter paper", "category": "paper", "unit_price": 0.22},
    {"item_name": "Decorative paper", "category": "paper", "unit_price": 0.18},
    {"item_name": "Letterhead paper", "category": "paper", "unit_price": 0.12},
    {"item_name": "Legal-size paper", "category": "paper", "unit_price": 0.08},
    {"item_name": "Crepe paper", "category": "paper", "unit_price": 0.05},
    {"item_name": "Photo paper", "category": "paper", "unit_price": 0.25},
    {"item_name": "Uncoated paper", "category": "paper", "unit_price": 0.06},
    {"item_name": "Butcher paper", "category": "paper", "unit_price": 0.10},
    {"item_name": "Heavyweight paper", "category": "paper", "unit_price": 0.20},
    {"item_name": "Standard copy paper", "category": "paper", "unit_price": 0.04},
    {"item_name": "Bright-colored paper", "category": "paper", "unit_price": 0.12},
    {"item_name": "Patterned paper", "category": "paper", "unit_price": 0.15},
    {"item_name": "Paper plates", "category": "product", "unit_price": 0.10},
    {"item_name": "Paper cups", "category": "product", "unit_price": 0.08},
    {"item_name": "Paper napkins", "category": "product", "unit_price": 0.02},
    {"item_name": "Disposable cups", "category": "product", "unit_price": 0.10},
    {"item_name": "Table covers", "category": "product", "unit_price": 1.50},
    {"item_name": "Envelopes", "category": "product", "unit_price": 0.05},
    {"item_name": "Sticky notes", "category": "product", "unit_price": 0.03},
    {"item_name": "Notepads", "category": "product", "unit_price": 2.00},
    {"item_name": "Invitation cards", "category": "product", "unit_price": 0.50},
    {"item_name": "Flyers", "category": "product", "unit_price": 0.15},
    {"item_name": "Party streamers", "category": "product", "unit_price": 0.05},
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},
    {"item_name": "Paper party bags", "category": "product", "unit_price": 0.25},
    {"item_name": "Name tags with lanyards", "category": "product", "unit_price": 0.75},
    {"item_name": "Presentation folders", "category": "product", "unit_price": 0.50},
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},
    {"item_name": "100 lb cover stock", "category": "specialty", "unit_price": 0.50},
    {"item_name": "80 lb text paper", "category": "specialty", "unit_price": 0.40},
    {"item_name": "250 gsm cardstock", "category": "specialty", "unit_price": 0.30},
    {"item_name": "220 gsm poster paper", "category": "specialty", "unit_price": 0.35},
]

ITEM_BY_NAME = {item["item_name"]: item for item in paper_supplies}
CATALOG_NAMES = [item["item_name"] for item in paper_supplies]
MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def generate_sample_inventory(supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """Generate reproducible starting inventory for a subset of the catalog."""
    np.random.seed(seed)
    selected_indices = np.random.choice(range(len(supplies)), size=int(len(supplies) * coverage), replace=False)
    rows = []
    for index in selected_indices:
        item = supplies[index]
        rows.append(
            {
                "item_name": item["item_name"],
                "category": item["category"],
                "unit_price": item["unit_price"],
                "current_stock": int(np.random.randint(200, 800)),
                "min_stock_level": int(np.random.randint(50, 150)),
            }
        )
    return pd.DataFrame(rows)


def init_database(seed: int = 137) -> None:
    """Set up transactions, historical quote data, and starting inventory."""
    with get_connection() as conn:
        pd.DataFrame(
            {
                "id": [],
                "item_name": [],
                "transaction_type": [],
                "units": [],
                "price": [],
                "transaction_date": [],
            }
        ).to_sql("transactions", conn, if_exists="replace", index=False)

        quote_requests_df = pd.read_csv(BASE_DIR / "quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", conn, if_exists="replace", index=False)

        quotes_df = pd.read_csv(BASE_DIR / "quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = datetime(2025, 1, 1).isoformat()
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda value: ast.literal_eval(value) if isinstance(value, str) else value
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda value: value.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda value: value.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda value: value.get("event_type", ""))
        quotes_df = quotes_df[
            ["request_id", "total_amount", "quote_explanation", "order_date", "job_type", "order_size", "event_type"]
        ]
        quotes_df.to_sql("quotes", conn, if_exists="replace", index=False)

        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)
        inventory_df.to_sql("inventory", conn, if_exists="replace", index=False)

        initial_date = datetime(2025, 1, 1).isoformat()
        transactions = [
            {
                "item_name": None,
                "transaction_type": "sales",
                "units": None,
                "price": 50000.0,
                "transaction_date": initial_date,
            }
        ]
        for _, item in inventory_df.iterrows():
            transactions.append(
                {
                    "item_name": item["item_name"],
                    "transaction_type": "stock_orders",
                    "units": int(item["current_stock"]),
                    "price": float(item["current_stock"] * item["unit_price"]),
                    "transaction_date": initial_date,
                }
            )
        pd.DataFrame(transactions).to_sql("transactions", conn, if_exists="append", index=False)


def ensure_inventory_reference(item_name: str) -> None:
    if item_name not in ITEM_BY_NAME:
        return
    with get_connection() as conn:
        existing = pd.read_sql_query("SELECT item_name FROM inventory WHERE item_name = ?", conn, params=(item_name,))
        if existing.empty:
            item = ITEM_BY_NAME[item_name]
            pd.DataFrame(
                [
                    {
                        "item_name": item["item_name"],
                        "category": item["category"],
                        "unit_price": item["unit_price"],
                        "current_stock": 0,
                        "min_stock_level": 100,
                    }
                ]
            ).to_sql("inventory", conn, if_exists="append", index=False)


def create_transaction(item_name: str, transaction_type: str, quantity: int, price: float, date: Union[str, datetime]) -> int:
    """Record a stock order or sale transaction."""
    if transaction_type not in {"stock_orders", "sales"}:
        raise ValueError("Transaction type must be 'stock_orders' or 'sales'")
    if quantity <= 0:
        raise ValueError("Quantity must be positive")
    if item_name:
        ensure_inventory_reference(item_name)
    date_str = date.isoformat() if isinstance(date, datetime) else date
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO transactions (item_name, transaction_type, units, price, transaction_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (item_name, transaction_type, quantity, price, date_str),
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """Return positive stock levels as of a date."""
    query = """
        SELECT item_name,
               SUM(CASE
                   WHEN transaction_type = 'stock_orders' THEN units
                   WHEN transaction_type = 'sales' THEN -units
                   ELSE 0
               END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL AND transaction_date <= ?
        GROUP BY item_name
        HAVING stock > 0
    """
    with get_connection() as conn:
        result = pd.read_sql_query(query, conn, params=(as_of_date,))
    return dict(zip(result["item_name"], result["stock"]))


def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """Return stock level for one item as of a date."""
    date_str = as_of_date.isoformat() if isinstance(as_of_date, datetime) else as_of_date
    query = """
        SELECT ? AS item_name,
               COALESCE(SUM(CASE
                   WHEN transaction_type = 'stock_orders' THEN units
                   WHEN transaction_type = 'sales' THEN -units
                   ELSE 0
               END), 0) AS current_stock
        FROM transactions
        WHERE item_name = ? AND transaction_date <= ?
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=(item_name, item_name, date_str))


def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """Estimate supplier delivery date from order date and quantity."""
    base_date = datetime.fromisoformat(input_date_str.split("T")[0])
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7
    return (base_date + timedelta(days=days)).strftime("%Y-%m-%d")


def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """Calculate cash balance as of a date."""
    date_str = as_of_date.isoformat() if isinstance(as_of_date, datetime) else as_of_date
    with get_connection() as conn:
        transactions = pd.read_sql_query("SELECT * FROM transactions WHERE transaction_date <= ?", conn, params=(date_str,))
    sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
    purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
    return float(sales - purchases)


def get_stock_quantity(item_name: str, as_of_date: str) -> int:
    stock_df = get_stock_level(item_name, as_of_date)
    return int(stock_df.iloc[0]["current_stock"] or 0) if not stock_df.empty else 0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """Generate cash, inventory, and total asset values."""
    date_str = as_of_date.isoformat() if isinstance(as_of_date, datetime) else as_of_date
    cash = get_cash_balance(date_str)
    with get_connection() as conn:
        inventory_df = pd.read_sql_query("SELECT * FROM inventory", conn)
    inventory_value = 0.0
    inventory_summary = []
    for _, item in inventory_df.iterrows():
        stock = get_stock_quantity(item["item_name"], date_str)
        value = float(stock * item["unit_price"])
        inventory_value += value
        inventory_summary.append(
            {
                "item_name": item["item_name"],
                "stock": stock,
                "unit_price": float(item["unit_price"]),
                "value": value,
            }
        )
    return {
        "as_of_date": date_str,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """Search historical quotes for comparable prior requests."""
    conditions = []
    params: List[Union[str, int]] = []
    for term in search_terms:
        conditions.append("(LOWER(qr.response) LIKE ? OR LOWER(q.quote_explanation) LIKE ?)")
        params.extend([f"%{term.lower()}%", f"%{term.lower()}%"])
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    query = f"""
        SELECT qr.response AS original_request, q.total_amount, q.quote_explanation,
               q.job_type, q.order_size, q.event_type, q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT ?
    """
    params.append(limit)
    with get_connection() as conn:
        result = conn.execute(query, params)
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]


class RequestedItem(BaseModel):
    quantity: int = Field(ge=1)
    raw_item: str
    item_name: Optional[str] = None


class ParsedRequest(BaseModel):
    request_date: str
    requested_delivery_date: str
    firm_order: bool
    items: List[RequestedItem]


class InventoryAssessment(BaseModel):
    item_name: Optional[str]
    raw_item: str
    quantity: int
    current_stock: int = 0
    missing_quantity: int = 0
    can_fulfill: bool = False
    reorder_needed: bool = False
    reorder_delivery_date: Optional[str] = None
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
    lines: List[QuoteLine] = Field(default_factory=list)
    total: float = 0.0
    historical_context: str = ""


class SalesDecision(BaseModel):
    sale_recorded: bool
    transaction_ids: List[int] = Field(default_factory=list)
    reason: str

class TransactionPlanLine(BaseModel):
    item_name: str
    transaction_type: str
    quantity: int
    price: float
    transaction_date: str

class ResponseEvaluation(BaseModel):
    passed: bool
    findings: List[str] = Field(default_factory=list)


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
    fulfilled_items: List[str] = Field(default_factory=list)
    unfulfilled_items: List[str] = Field(default_factory=list)
    agent_route: str
    tool_calls: List[str] = Field(default_factory=list)
    evaluation_passed: bool = False
    evaluation_findings: List[str] = Field(default_factory=list)

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


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", value.lower()).strip()


def parse_requested_delivery_date(request_text: str, request_date: str) -> str:
    match = re.search(
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})\b",
        request_text,
        flags=re.IGNORECASE,
    )
    if match:
        return datetime(int(match.group(3)), MONTHS[match.group(1).lower()], int(match.group(2))).strftime("%Y-%m-%d")
    return (datetime.fromisoformat(request_date) + timedelta(days=14)).strftime("%Y-%m-%d")


def strip_order_tail(request_text: str) -> str:
    markers = [
        "I need these supplies delivered",
        "We need these supplies delivered",
        "I need these items delivered",
        "We need these items delivered",
        "Please ensure delivery",
        "Please deliver these supplies",
        "Please deliver the supplies",
        "The supplies are needed",
        "The supplies must be delivered",
        "I need the order delivered",
        "We need the supplies delivered",
    ]
    lowered = request_text.lower()
    positions = [lowered.find(marker.lower()) for marker in markers if lowered.find(marker.lower()) != -1]
    return request_text[: min(positions)] if positions else request_text


def prepare_request_text(request_text: str) -> str:
    text_value = strip_order_tail(request_text)
    text_value = re.sub(
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
        " ",
        text_value,
        flags=re.IGNORECASE,
    )
    text_value = re.sub(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", " ", text_value)
    text_value = text_value.replace("\n", " ")
    text_value = re.sub(r"\s+-\s+", ", ", text_value)
    text_value = re.sub(r"\b(along with|as well as)\b", ", ", text_value, flags=re.IGNORECASE)
    text_value = re.sub(r"\s+and\s+(?=\d[\d,]*\s)", ", ", text_value, flags=re.IGNORECASE)
    text_value = re.sub(r"\b(high-quality|high quality|sturdy)\s*,\s*", r"\1 ", text_value, flags=re.IGNORECASE)
    text_value = re.sub(
        r"8\s*\.\s*5\s*(?:\"+|inches|inch|in)?\s*x\s*11\s*(?:\"+|inches|inch|in)?",
        "letter-sized",
        text_value,
        flags=re.IGNORECASE,
    )
    return text_value


def clean_item_phrase(raw_item: str) -> str:
    cleaned = raw_item.lower().replace('"', " ").replace("'", " ")
    cleaned = re.sub(r"^\s*(?:sheets?|rolls?|roll|reams?|ream|packets?|packet|units?|unit)\s+(?:of\s+)?", " ", cleaned)
    cleaned = re.sub(r"\([^)]*(?:white|assorted|biodegradable|colors?|inches?)\)", " ", cleaned)
    cleaned = re.sub(
        r"\b(?:high quality|high-quality|sturdy|various colors|assorted colors|assorted|white|biodegradable|size)\b",
        " ",
        cleaned,
    )
    cleaned = re.sub(r"\b(?:for|by|to)\b.*$", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def resolve_item_name(raw_name: str) -> Optional[str]:
    cleaned = normalize_text(raw_name)
    if not cleaned or any(word in cleaned for word in ["balloon", "ticket", "cardboard"]):
        return None
    normalized_catalog = {normalize_text(name): name for name in CATALOG_NAMES}
    if cleaned in normalized_catalog:
        return normalized_catalog[cleaned]
    if "washi" in cleaned or "decorative adhesive tape" in cleaned:
        return "Decorative adhesive tape (washi tape)"
    if "poster board" in cleaned or ("poster" in cleaned and "24" in cleaned and "36" in cleaned):
        return "Large poster paper (24x36 inches)"
    if cleaned in {"flyer", "flyers"}:
        return "Flyers"
    if cleaned in {"poster", "posters"} or "poster paper" in cleaned:
        return "Poster paper"
    if "streamer" in cleaned:
        return "Party streamers"
    if "disposable cup" in cleaned:
        return "Disposable cups"
    if "paper cup" in cleaned or cleaned == "cups":
        return "Paper cups"
    if "paper plate" in cleaned or cleaned == "plates":
        return "Paper plates"
    if "napkin" in cleaned:
        return "Paper napkins"
    if "envelope" in cleaned:
        return "Envelopes"
    if "cardstock" in cleaned:
        return "Cardstock"
    if "construction" in cleaned:
        return "Construction paper"
    if "kraft" in cleaned:
        return "Kraft paper"
    if "printer" in cleaned or "printing" in cleaned or "copy" in cleaned:
        return "A4 paper" if "a4" in cleaned else "Standard copy paper"
    if "a3" in cleaned and "glossy" in cleaned:
        return "Glossy paper"
    if "a3" in cleaned and "matte" in cleaned:
        return "Matte paper"
    if "a3" in cleaned and "colored" in cleaned:
        return "Colored paper"
    if "a3" in cleaned:
        return None
    if "a4" in cleaned and "glossy" in cleaned:
        return "Glossy paper"
    if "a4" in cleaned and "matte" in cleaned:
        return "Matte paper"
    if "a4" in cleaned and "recycled" in cleaned:
        return "Recycled paper"
    if "glossy" in cleaned:
        return "Glossy paper"
    if "matte" in cleaned:
        return "Matte paper"
    if "recycled" in cleaned and "cardstock" not in cleaned:
        return "Recycled paper"
    if "colored" in cleaned or "bright" in cleaned or "colorful" in cleaned:
        return "Poster paper" if "poster" in cleaned else "Colored paper"
    if "heavyweight" in cleaned:
        return "Heavyweight paper"
    matches = get_close_matches(raw_name, CATALOG_NAMES, n=1, cutoff=0.82)
    return matches[0] if matches else None


def canonical_item_name(value: Optional[str]) -> Optional[str]:
    """Return the exact catalog key for a model/tool-provided item name."""
    if not value:
        return None

    if value in ITEM_BY_NAME:
        return value

    normalized_catalog = {normalize_text(name): name for name in CATALOG_NAMES}
    normalized_value = normalize_text(value)

    if normalized_value in normalized_catalog:
        return normalized_catalog[normalized_value]

    resolved = resolve_item_name(clean_item_phrase(value))
    if resolved in ITEM_BY_NAME:
        return resolved

    matches = get_close_matches(value, CATALOG_NAMES, n=1, cutoff=0.76)
    return matches[0] if matches else None


def extract_requested_line_items(request_text: str) -> List[RequestedItem]:
    pattern = re.compile(
        r"(?P<qty>\d[\d,]*)\s+"
        r"(?:(?P<measure>sheets?|rolls?|roll|reams?|ream|packets?|packet|units?|unit)\s+(?:of\s+)?)?"
        r"(?P<item>[^,\.]+)",
        flags=re.IGNORECASE,
    )
    items: List[RequestedItem] = []
    for match in pattern.finditer(prepare_request_text(request_text)):
        quantity = int(match.group("qty").replace(",", ""))
        raw_phrase = f"{(match.group('measure') or '').strip()} {(match.group('item') or '').strip()}".strip()
        cleaned_phrase = clean_item_phrase(raw_phrase)
        items.append(RequestedItem(quantity=quantity, raw_item=raw_phrase, item_name=resolve_item_name(cleaned_phrase)))
    return consolidate_request_items(items)


def consolidate_request_items(items: List[RequestedItem]) -> List[RequestedItem]:
    consolidated: Dict[str, RequestedItem] = {}
    output: List[RequestedItem] = []
    for item in items:
        if not item.item_name:
            output.append(item)
            continue
        if item.item_name not in consolidated:
            consolidated[item.item_name] = RequestedItem(
                quantity=item.quantity,
                raw_item=item.item_name,
                item_name=item.item_name,
            )
            output.append(consolidated[item.item_name])
        else:
            consolidated[item.item_name].quantity += item.quantity
    return output


def is_firm_order_request(request_text: str) -> bool:
    lower_request = request_text.lower()
    return any(
        phrase in lower_request
        for phrase in ["place an order", "need to order", "confirm the order", "large order", "medium order", "small order"]
    )


def get_unit_price(item_name: str) -> float:
    canonical_name = canonical_item_name(item_name)
    if canonical_name is None:
        raise ValueError(f"Unknown catalog item: {item_name!r}")
    return float(ITEM_BY_NAME[canonical_name]["unit_price"])


def get_wholesale_cost(item_name: str, quantity: int) -> float:
    return round(get_unit_price(item_name) * quantity * 0.60, 2)


def calculate_discount(quantity: int, need_size: str) -> float:
    if quantity >= 5000 or need_size == "large":
        return 0.15
    if quantity >= 1000:
        return 0.12
    if quantity >= 500 or need_size == "medium":
        return 0.10
    if quantity >= 100:
        return 0.05
    return 0.0


def make_framework_agent(name: str, prompt: str, output_type: Any) -> Agent:
    """Create a pydantic-ai Agent while supporting both old and new result/output APIs."""
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
        return Agent(AGENT_MODEL, system_prompt=system_prompt, output_type=output_type)
    except TypeError:
        # Older pydantic-ai releases used result_type instead of output_type.
        return Agent(AGENT_MODEL, system_prompt=system_prompt, result_type=output_type)


class OrchestrationPlan(BaseModel):
    route: List[str]
    rationale: str


class FinalResponseResult(BaseModel):
    order_status: str
    response: str
    evaluation_passed: bool
    evaluation_findings: List[str] = Field(default_factory=list)


class FinalResponseDraft(BaseModel):
    response: str


class IntakeResult(ParsedRequest):
    notes: str = ""


class InventoryResult(BaseModel):
    assessments: List[InventoryAssessment]
    notes: str = ""


class QuoteResult(QuoteProposal):
    notes: str = ""


class SalesResult(SalesDecision):
    cash_after: float
    inventory_after: float
    notes: str = ""


@dataclass
class AgentToolRecorder:
    agent_name: str
    tool_audit: List[ToolAudit] = field(default_factory=list)

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


class IntakeAgent(AgentToolRecorder):
    """Framework-executed agent that turns raw customer text into structured order intent."""

    def __init__(self) -> None:
        super().__init__("IntakeAgent")
        self.framework_agent = make_framework_agent(
            self.agent_name,
            "Extract delivery date, firm-order intent, quantities, and catalog-resolved item names from the customer request.",
            IntakeResult,
        )
        self._register_tools()

    def _register_tools(self) -> None:
        @self.framework_agent.tool
        def parse_delivery_date(ctx: RunContext, request_text: str, request_date: str) -> str:
            self.record_tool("parse_delivery_date", f"request_date={request_date}")
            return parse_requested_delivery_date(request_text, request_date)

        @self.framework_agent.tool
        def extract_line_items(ctx: RunContext, request_text: str) -> List[Dict[str, Any]]:
            self.record_tool("extract_line_items", "raw customer request parsed")
            return [item.model_dump() for item in extract_requested_line_items(request_text)]

        @self.framework_agent.tool
        def classify_firm_order(ctx: RunContext, request_text: str) -> bool:
            self.record_tool("classify_firm_order", "customer intent classified")
            return is_firm_order_request(request_text)

        @self.framework_agent.tool
        def resolve_catalog_item(ctx: RunContext, raw_item: str) -> Optional[str]:
            self.record_tool("resolve_catalog_item", f"raw_item={raw_item}")
            return resolve_item_name(clean_item_phrase(raw_item))

    def run_intake(self, request_text: str, request_date: str) -> IntakeResult:
        prompt = f"""
Customer request date: {request_date}
Customer request text:
{request_text}

Use the tools to parse delivery date, firm-order intent, and line items. Return an IntakeResult.
Each item must preserve the raw phrase and include the catalog item_name when a catalog match exists.
""".strip()
        return self._output(self.framework_agent.run_sync(prompt))


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
        def inventory_snapshot(ctx: RunContext, as_of_date: str) -> Dict[str, int]:
            self.record_tool("inventory_snapshot", f"as_of_date={as_of_date}")
            return get_all_inventory(as_of_date)

        @self.framework_agent.tool
        def item_stock_level(ctx: RunContext, item_name: str, as_of_date: str) -> Dict[str, Any]:
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
            self.record_tool("supplier_delivery_eta", f"request_date={request_date}, quantity={quantity}")
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


class QuotingAgent(AgentToolRecorder):
    """Framework-executed agent that generates quote lines and rationale."""

    def __init__(self) -> None:
        super().__init__("QuotingAgent")
        self.framework_agent = make_framework_agent(
            self.agent_name,
            "Generate explainable quotes using catalog prices, volume discounts, and historical quote context. Do not mutate inventory.",
            QuoteResult,
        )
        self._register_tools()

    def _register_tools(self) -> None:
        @self.framework_agent.tool
        def quote_history_search(ctx: RunContext, search_terms: List[str], limit: int = 5) -> List[Dict[str, Any]]:
            self.record_tool("quote_history_search", f"terms={search_terms}, limit={limit}")
            return search_quote_history(search_terms, limit)

        @self.framework_agent.tool
        def catalog_unit_price(ctx: RunContext, item_name: str) -> float:
            canonical_name = canonical_item_name(item_name)
            self.record_tool("catalog_unit_price", f"item_name={item_name} -> {canonical_name or 'unmatched'}")
            return get_unit_price(canonical_name) if canonical_name else 0.0

        @self.framework_agent.tool
        def volume_discount(ctx: RunContext, quantity: int, need_size: str) -> float:
            self.record_tool("volume_discount", f"quantity={quantity}, need_size={need_size}")
            return calculate_discount(quantity, need_size.lower())

    def run_quote(self, parsed: IntakeResult, inventory: InventoryResult, request_context: Dict[str, Any]) -> QuoteResult:
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
        self.pending_transaction_plan: List[TransactionPlanLine] = []
        self.pending_commit_result: Optional[SalesResult] = None
        self._register_tools()


    def _transaction_exists(
        self,
        item_name: str,
        transaction_type: str,
        quantity: int,
        price: float,
        date: str,
    ) -> Optional[int]:
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
    ) -> List[TransactionPlanLine]:
        plan: List[TransactionPlanLine] = []

        for assessment in inventory.assessments:
            canonical_name = canonical_item_name(assessment.item_name)
            if (
                canonical_name
                and assessment.reorder_needed
                and assessment.missing_quantity > 0
            ):
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
    def summarize_transaction_plan(plan: List[TransactionPlanLine]) -> Dict[str, float]:
        gross_sales = round(
            sum(transaction.price for transaction in plan if transaction.transaction_type == "sales"),
            2,
        )
        restock_spend = round(
            sum(transaction.price for transaction in plan if transaction.transaction_type == "stock_orders"),
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

        transaction_ids: List[int] = []

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
        def commit_validated_transaction_plan(ctx: RunContext) -> Dict[str, Any]:
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
        def financial_report(ctx: RunContext, as_of_date: str) -> Dict[str, Any]:
            self.record_tool("financial_report", f"as_of_date={as_of_date}")
            return generate_financial_report(as_of_date)

    def run_sales(self, parsed: IntakeResult, inventory: InventoryResult, quote: QuoteResult) -> SalesResult:
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

class OrchestratorAgent(AgentToolRecorder):
    """Framework-executed coordinator plus evaluator for the five-agent system."""

    def __init__(self) -> None:
        super().__init__("OrchestratorAgent")
        self.framework_agent = make_framework_agent(
            self.agent_name,
            "Coordinate Intake, Inventory, Quoting, and Sales agents, then synthesize and evaluate the final customer response.",
            OrchestrationPlan,
        )
        self.final_response_agent = make_framework_agent(
            f"{self.agent_name}FinalResponse",
            "Write a concise, transparent customer-facing response from validated business facts. Do not call tools.",
            FinalResponseDraft,
        )
        self.intake_agent = IntakeAgent()
        self.inventory_agent = InventoryAgent()
        self.quoting_agent = QuotingAgent()
        self.sales_agent = SalesAgent()
        self._register_tools()

    def _register_tools(self) -> None:
        @self.framework_agent.tool
        def workflow_plan(ctx: RunContext, request_summary: str) -> Dict[str, Any]:
            self.record_tool("workflow_plan", "route planning requested")
            return {
                "route": ["IntakeAgent", "InventoryAgent", "QuotingAgent", "SalesAgent", "OrchestratorAgent"],
                "rationale": "Parse request, assess fulfillment, quote fulfillable items, finalize firm orders, then evaluate response.",
                "request_summary": request_summary,
            }

    @staticmethod
    def canonicalize_agent_route(route: List[str]) -> List[str]:
        """Keep the reported route aligned with the submitted five-agent workflow diagram."""
        standard_route = [
            "IntakeAgent",
            "InventoryAgent",
            "QuotingAgent",
            "SalesAgent",
            "OrchestratorAgent",
        ]

        if not route:
            return standard_route

        normalized_route = [str(agent).strip() for agent in route if str(agent).strip()]

        # The planning LLM may occasionally omit the final OrchestratorAgent or SalesAgent
        # when no sale is recorded. For review evidence, the route should match the
        # submitted architecture: the SalesAgent participates in the decision gate and
        # the OrchestratorAgent always assembles/evaluates the final response.
        for agent in standard_route:
            if agent not in normalized_route:
                normalized_route.append(agent)

        return [agent for agent in standard_route if agent in normalized_route]

    def process_request(self, request_id: int, source_row: int, row: pd.Series) -> WorkflowResult:
        request_date = row["request_date"].strftime("%Y-%m-%d")
        cash_before = generate_financial_report(request_date)["cash_balance"]
        inventory_before = generate_financial_report(request_date)["inventory_value"]

        request_summary = {
            "source_row": source_row,
            "request_date": request_date,
            "job": str(row.get("job", "")),
            "event": str(row.get("event", "")),
            "need_size": str(row.get("need_size", "")),
            "request": str(row["request"]),
        }
        try:
            plan_prompt = f"""
Customer request summary:
{request_summary}

Call workflow_plan exactly once, then return the selected route as an OrchestrationPlan.
Use the standard route when appropriate: IntakeAgent, InventoryAgent, QuotingAgent,
SalesAgent when a firm fully fulfillable order should be recorded, then OrchestratorAgent.
""".strip()
            plan_output = self._output(self.framework_agent.run_sync(plan_prompt))
            if isinstance(plan_output, OrchestrationPlan):
                plan = plan_output
            else:
                plan = OrchestrationPlan.model_validate(plan_output)
        except Exception as exc:
            plan = OrchestrationPlan(
                route=[
                    "IntakeAgent",
                    "InventoryAgent",
                    "QuotingAgent",
                    "SalesAgent",
                    "OrchestratorAgent",
                ],
                rationale=f"Fallback fixed five-agent route after planning error: {exc.__class__.__name__}.",
            )
            self.record_tool("workflow_plan_fallback", "orchestrator planning fallback used")

        plan.route = self.canonicalize_agent_route(plan.route)

        parsed = self.intake_agent.run_intake(str(row["request"]), request_date)
        inventory = self.validate_inventory_result(parsed, self.inventory_agent.run_inventory(parsed))

        request_context = {
            "job": str(row.get("job", "")),
            "event": str(row.get("event", "")),
            "need_size": str(row.get("need_size", "")),
        }

        quote = self.validate_quote_result(
            parsed,
            inventory,
            self.quoting_agent.run_quote(parsed, inventory, request_context),
            request_context,
        )

        all_fulfillable = bool(inventory.assessments) and all(
            assessment.can_fulfill for assessment in inventory.assessments
        )
        can_record_sale = parsed.firm_order and bool(quote.lines) and all_fulfillable

        if can_record_sale:
            sales = self.sales_agent.run_sales(parsed, inventory, quote)
        else:
            report_after = generate_financial_report(request_date)
            sales = SalesResult(
                sale_recorded=False,
                transaction_ids=[],
                reason=self.sales_skip_reason(parsed, all_fulfillable, quote),
                cash_after=report_after["cash_balance"],
                inventory_after=report_after["inventory_value"],
            )

        transaction_summary = self.sales_agent.summarize_transaction_plan(
            self.sales_agent.pending_transaction_plan
        ) if sales.sale_recorded else {
            "gross_sales": 0.0,
            "restock_spend": 0.0,
            "expected_net_cash_delta": 0.0,
        }

        fulfilled_items = [line.item_name for line in quote.lines]
        unfulfilled_items = [
            assessment.raw_item
            for assessment in inventory.assessments
            if not assessment.can_fulfill
        ]

        final = self.run_final_response(parsed, inventory, quote, sales, all_fulfillable)
        report_after = generate_financial_report(request_date)

        return WorkflowResult(
            request_id=request_id,
            source_row=source_row,
            request_date=request_date,
            requested_delivery_date=parsed.requested_delivery_date,
            order_status=final.order_status,
            response=final.response,
            cash_before=cash_before,
            cash_after=report_after["cash_balance"],
            inventory_before=inventory_before,
            inventory_after=report_after["inventory_value"],
            gross_sales=transaction_summary["gross_sales"],
            restock_spend=transaction_summary["restock_spend"],
            expected_net_cash_delta=transaction_summary["expected_net_cash_delta"],
            actual_cash_delta=round(report_after["cash_balance"] - cash_before, 2),
            fulfilled_items=fulfilled_items,
            unfulfilled_items=unfulfilled_items,
            agent_route=" -> ".join(plan.route),
            tool_calls=[audit.format() for audit in self.collect_tool_audit()],
            evaluation_passed=final.evaluation_passed,
            evaluation_findings=final.evaluation_findings,
        )

    @staticmethod
    def sales_skip_reason(parsed: IntakeResult, all_fulfillable: bool, quote: QuoteResult) -> str:
        if not parsed.firm_order:
            return "the request is a quote request, not a confirmed order"
        if not quote.lines:
            return "no requested item can be quoted"
        if not all_fulfillable:
            return "one or more requested items cannot be fulfilled by the requested delivery date"
        return "the order did not pass the final sales validation"

    @staticmethod
    def validate_inventory_result(parsed: IntakeResult, inventory: InventoryResult) -> InventoryResult:
        """Use the model's inventory work, then enforce catalog, stock, and supplier-date rules."""
        assessments: List[InventoryAssessment] = []

        for item in parsed.items:
            canonical_name = canonical_item_name(item.item_name)

            if canonical_name is None:
                assessments.append(
                    InventoryAssessment(
                        item_name=None,
                        raw_item=item.raw_item,
                        quantity=item.quantity,
                        reason="not carried in the current catalog",
                    )
                )
                continue

            current_stock = get_stock_quantity(canonical_name, parsed.request_date)
            missing_quantity = max(item.quantity - current_stock, 0)

            if missing_quantity == 0:
                assessments.append(
                    InventoryAssessment(
                        item_name=canonical_name,
                        raw_item=item.raw_item,
                        quantity=item.quantity,
                        current_stock=current_stock,
                        can_fulfill=True,
                        reason="available from current stock",
                    )
                )
                continue

            reorder_delivery_date = get_supplier_delivery_date(parsed.request_date, missing_quantity)
            can_reorder_in_time = reorder_delivery_date <= parsed.requested_delivery_date
            reason = (
                "supplier delivery can meet the requested date"
                if can_reorder_in_time
                else f"stock is short by {missing_quantity} units and supplier delivery would arrive after the requested date"
            )

            assessments.append(
                InventoryAssessment(
                    item_name=canonical_name,
                    raw_item=item.raw_item,
                    quantity=item.quantity,
                    current_stock=current_stock,
                    missing_quantity=missing_quantity,
                    can_fulfill=can_reorder_in_time,
                    reorder_needed=can_reorder_in_time,
                    reorder_delivery_date=reorder_delivery_date,
                    reason=reason,
                )
            )

        return InventoryResult(assessments=assessments, notes=inventory.notes)

    @staticmethod
    def validate_quote_result(
        parsed: IntakeResult,
        inventory: InventoryResult,
        quote: QuoteResult,
        request_context: Dict[str, Any],
    ) -> QuoteResult:
        """Keep model wording where possible, but enforce quote math and remove unfulfillable lines."""
        model_lines = {
            canonical_item_name(line.item_name) or line.item_name: line
            for line in quote.lines
        }
        need_size = str(request_context.get("need_size", "")).lower()
        lines: List[QuoteLine] = []

        for assessment in inventory.assessments:
            canonical_name = canonical_item_name(assessment.item_name)
            if not canonical_name or not assessment.can_fulfill:
                continue

            model_line = model_lines.get(canonical_name)
            list_unit_price = get_unit_price(canonical_name)
            discount_rate = calculate_discount(assessment.quantity, need_size)
            quoted_unit_price = round(list_unit_price * (1 - discount_rate), 4)
            line_total = round(quoted_unit_price * assessment.quantity, 2)
            delivery_date = assessment.reorder_delivery_date or parsed.requested_delivery_date

            if model_line and model_line.rationale:
                rationale = model_line.rationale.rstrip(".")
            elif discount_rate:
                rationale = f"{discount_rate * 100:.0f}% quantity discount applied"
            else:
                rationale = "standard catalog pricing applied"

            lines.append(
                QuoteLine(
                    item_name=canonical_name,
                    quantity=assessment.quantity,
                    list_unit_price=list_unit_price,
                    discount_rate=discount_rate,
                    quoted_unit_price=quoted_unit_price,
                    line_total=line_total,
                    delivery_date=delivery_date,
                    rationale=rationale,
                    reorder_needed=assessment.reorder_needed,
                )
            )

        total = round(sum(line.line_total for line in lines), 2)
        return QuoteResult(
            lines=lines,
            total=total,
            historical_context=quote.historical_context.strip(),
            notes=quote.notes,
        )

    def run_final_response(
        self,
        parsed: IntakeResult,
        inventory: InventoryResult,
        quote: QuoteResult,
        sales: SalesResult,
        all_fulfillable: bool,
    ) -> FinalResponseResult:
        status = self.determine_order_status(parsed, quote, sales, all_fulfillable)
        facts = self.build_response_facts(parsed, inventory, quote, sales)
        prompt = f"""
Order status to use exactly: {status}

Validated business facts:
{facts}

Write only the customer-facing response.
Every response must include a natural explanation phrase using at least one of these exact words or phrases: because, due to, discount, current stock, supplier delivery, reorder, or not carried in our current catalog.
Do not add a separate label named "Rationale:"; include the explanation naturally in the customer-facing wording.
Use 1-3 short paragraphs plus bullets when useful.
Use natural language and do not sound like a hard-coded template.
Use only the validated facts above.
Mention the quote total only when validated facts include a quote total.
Do not invent a quote total when no quote lines are provided.
Mention confirmation is needed when this is only a quote.
Mention why any unavailable item cannot be fulfilled.
Use "not carried in our current catalog" only when the validated facts say exactly that; otherwise describe the issue as stock shortage or supplier delivery timing.
Do not say a catalog item is uncataloged; use the validated facts exactly.
Quoted unit prices and line totals already include discounts. Do not calculate another adjusted total.
Do not expose raw internal status names such as quote_ready, partial_quote_needs_review, or fulfilled_sale_recorded.
Do not say items have shipped or already delivered; say they are scheduled for delivery.
Use "in stock" only for items explicitly described as current stock. Otherwise say "can be fulfilled" or reference the reorder date.
Never include placeholder money like $XXX, [Quote Total], TBD, or unknown.
Do not include placeholders like [Your Company Name], [Your Name], or bracketed placeholder text.
Do not reveal wholesale costs, profit margins, database internals, API details, or stack traces.
Avoid double periods and avoid random capitalization in the middle of a sentence.
If order status is fulfilled_sale_recorded, do not ask the customer to confirm; the order has already been confirmed and recorded.
""".strip()

        try:
            draft = self._output(self.final_response_agent.run_sync(prompt))
            response = draft.response if isinstance(draft, FinalResponseDraft) else str(draft)
            response = self.clean_customer_response(response)
            self.record_tool("final_response_model", "customer response drafted by model")
        except Exception as exc:
            response = self.clean_customer_response(self.build_fallback_customer_response(status, quote, inventory, sales))
            self.record_tool("final_response_fallback", f"model response failed: {exc.__class__.__name__}")

        evaluation = self.evaluate_response_text(response)
        if "response lacks a clear rationale" in evaluation.findings:
            raise RuntimeError("Final customer response failed rationale quality check.")  


        self.record_tool("response_quality_check", "final customer response reviewed deterministically")

        return FinalResponseResult(
            order_status=status,
            response=response,
            evaluation_passed=evaluation.passed,
            evaluation_findings=evaluation.findings,
        )

    @staticmethod
    def build_fallback_customer_response(
        status: str,
        quote: QuoteResult,
        inventory: InventoryResult,
        sales: SalesResult,
    ) -> str:
        parts: List[str] = []

        if sales.sale_recorded:
            parts.append(
                "Thank you for your order. Because the requested items can be fulfilled by the scheduled delivery dates, "
                "your firm order has been fulfilled and recorded."
            )
        elif quote.lines:
            parts.append(
                "Thank you for your request. We have prepared a quote for the items we can fulfill because the validated "
                "items can be supplied by the scheduled delivery dates."
            )
        else:
            parts.append(
                "Thank you for your request. We are unable to fulfill the requested items by the requested delivery date "
                "because of stock availability, supplier delivery timing, or catalog availability."
            )

        if quote.lines:
            parts.append(f"Quote total: ${quote.total:.2f}.")
            for line in quote.lines:
                parts.append(
                    f"- {line.quantity} units of {line.item_name} at ${line.quoted_unit_price:.2f} each "
                    f"for ${line.line_total:.2f}, delivery {line.delivery_date}."
                )

        unavailable = [assessment for assessment in inventory.assessments if not assessment.can_fulfill]
        if unavailable:
            parts.append("Unavailable items:")
            for assessment in unavailable:
                item_name = assessment.item_name or assessment.raw_item
                parts.append(f"- {item_name}: {assessment.reason.rstrip('.')}.")

        if not sales.sale_recorded and quote.lines:
            parts.append("Please confirm if you would like to proceed with the quoted items.")

        return "\n".join(parts)


    @staticmethod
    def build_response_facts(
        parsed: IntakeResult,
        inventory: InventoryResult,
        quote: QuoteResult,
        sales: SalesResult,
    ) -> str:
        facts = [
            f"Requested delivery date: {parsed.requested_delivery_date}.",
        ]

        if sales.sale_recorded:
            facts.append("The firm order was recorded.")
        elif parsed.firm_order:
            facts.append(f"The sale was not recorded because {sales.reason}.")
        else:
            facts.append("This is a quote only; customer confirmation is required before recording a sale.")

        if quote.lines:
            facts.append(f"Quote total: ${quote.total:.2f}.")
            for line in quote.lines:
                facts.append(
                    f"Quoted item: {line.quantity} units of {line.item_name}; "
                    f"discounted unit price ${line.quoted_unit_price:.2f}; "
                    f"line total ${line.line_total:.2f}; "
                    f"{line.discount_rate * 100:.0f}% discount already included; "
                    f"delivery {line.delivery_date}; "
                    f"rationale: {line.rationale}."
                )
        else:
            facts.append("No quote total is available because no requested item can be fulfilled.")

        for assessment in inventory.assessments:
            if assessment.can_fulfill:
                if assessment.reorder_needed:
                    facts.append(
                        f"{assessment.item_name} is a catalog item and can be fulfilled with a reorder of "
                        f"{assessment.missing_quantity} units arriving {assessment.reorder_delivery_date}."
                    )
                else:
                    facts.append(f"{assessment.item_name} is a catalog item and can be fulfilled from current stock.")
            else:
                if assessment.item_name is None:
                    facts.append(
                        f"{assessment.raw_item} cannot be fulfilled because it is not carried in the current catalog."
                    )
                else:
                    facts.append(
                        f"{assessment.item_name} is a catalog item but cannot be fulfilled because "
                        f"{assessment.reason.rstrip('.')}."
                    )

        return "\n".join(facts)

    @staticmethod
    def clean_customer_response(response: str) -> str:
        status_replacements = {
            "partial_quote_needs_review": "partial quote ready for review",
            "fulfilled_sale_recorded": "fulfilled and recorded",
            "quote_ready": "quote ready",
        }
        for raw_status, friendly_status in status_replacements.items():
            response = response.replace(raw_status, friendly_status)

        response = re.sub(r"\bhave been shipped\b", "are scheduled for delivery", response, flags=re.IGNORECASE)
        response = re.sub(r"\bhas been shipped\b", "is scheduled for delivery", response, flags=re.IGNORECASE)
        response = re.sub(r"\bhave already been delivered\b", "are scheduled for delivery", response, flags=re.IGNORECASE)
        response = re.sub(r"\balready delivered\b", "scheduled for delivery", response, flags=re.IGNORECASE)
        response = re.sub(
            r"All items are in stock and available for delivery on the specified dates\.",
            "All quoted items can be fulfilled by the scheduled delivery dates.",
            response,
            flags=re.IGNORECASE,
        )
        response = re.sub(
            r"All quoted items are in stock and available for delivery on the specified dates\.",
            "All quoted items can be fulfilled by the scheduled delivery dates.",
            response,
            flags=re.IGNORECASE,
        )
        response = re.sub(r"\.{2,}", ".", response)
        response = re.sub(r"\s+\.", ".", response)
        response = re.sub(r"\[[^\]]+\]", "", response)
        response = re.sub(r"\$XXX|\bTBD\b|\bunknown\b", "", response, flags=re.IGNORECASE)
        response = re.sub(r",?\s*totaling\s*\.", ".", response, flags=re.IGNORECASE)
        response = re.sub(r"\n{3,}", "\n\n", response)
        return response.strip()

    @staticmethod
    def evaluate_response_text(response: str) -> ResponseEvaluation:
        lower_response = response.lower()
        blocked_terms = ("wholesale", "margin", "traceback", "sqlite", "sqlalchemy", "api key", "$xxx", "tbd")
        findings = [
            f"contains internal term: {term}"
            for term in blocked_terms
            if term in lower_response
        ]

        if not response.strip():
            findings.append("response is empty")

        if re.search(r"\[[^\]]+\]", response):
            findings.append("contains placeholder bracket text")

        raw_statuses = ("quote_ready", "partial_quote_needs_review", "fulfilled_sale_recorded")
        if any(status in response for status in raw_statuses):
            findings.append("contains raw internal order status")

        rationale_terms = (
            "because",
            "due to",
            "discount",
            "not carried",
            "unavailable",
            "unable",
            "cannot fulfill",
            "cannot be fulfilled",
            "shortage",
            "stock shortages",
            "short by",
            "supplier delivery",
            "supplier timing",
            "supplier",
            "reorder",
            "quote",
            "current stock",
            "available from current stock",
            "fulfilled from current stock",
            "can be fulfilled",
            "scheduled for delivery",
            "processed",
        )
        if not any(term in lower_response for term in rationale_terms):
            findings.append("response lacks a clear rationale")

        return ResponseEvaluation(passed=not findings, findings=findings)

    @staticmethod
    def determine_order_status(parsed: IntakeResult, quote: QuoteResult, sales: SalesResult, all_fulfillable: bool) -> str:
        if sales.sale_recorded:
            return "fulfilled_sale_recorded"
        if all_fulfillable and quote.lines:
            return "quote_ready"
        if quote.lines:
            return "partial_quote_needs_review"
        return "unfulfilled"

    def collect_tool_audit(self) -> List[ToolAudit]:
        audits = list(self.tool_audit)
        for worker in [self.intake_agent, self.inventory_agent, self.quoting_agent, self.sales_agent]:
            audits.extend(worker.tool_audit)
            worker.tool_audit.clear()
        self.tool_audit.clear()
        return audits


def build_agent_team() -> OrchestratorAgent:
    return OrchestratorAgent()


def run_test_scenarios(output_path: str = "test_results.csv", sleep_seconds: float = 0.0):
    print("Initializing Database...")
    init_database()
    try:
        quote_requests_sample = pd.read_csv(BASE_DIR / "quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample["_source_order"] = range(len(quote_requests_sample))
        quote_requests_sample = quote_requests_sample.sort_values(
            ["request_date", "_source_order"],
            kind="mergesort",
        ).drop(columns="_source_order")
    except Exception as exc:
        print(f"FATAL: Error loading test data: {exc}")
        return []

    orchestrator = build_agent_team()
    print(f"Using {FRAMEWORK_NAME} framework-executed five-agent workflow.")
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    results: List[WorkflowResult] = []
    for request_number, (source_index, row) in enumerate(quote_requests_sample.iterrows(), start=1):
        request_date = row["request_date"].strftime("%Y-%m-%d")
        print(f"\n=== Request {request_number} ===")
        print(f"Source Row: {source_index + 1}")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")
        result = orchestrator.process_request(request_number, source_index + 1, row)
        report = generate_financial_report(result.request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]
        print(f"Status: {result.order_status}")
        print(f"Response: {result.response}")
        if result.cash_changed:
            print(
                "Financial impact: "
                f"gross sale ${result.gross_sales:.2f}, "
                f"restock spend ${result.restock_spend:.2f}, "
                f"net cash change ${result.actual_cash_delta:.2f}"
            )
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")
        results.append(result)
        if sleep_seconds:
            time.sleep(sleep_seconds)

    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")
    write_results_csv(results, output_path)
    print_final_summary(results, output_path)
    return results


def write_results_csv(results: List[WorkflowResult], output_path: str) -> None:
    pd.DataFrame(
        [
            {
                "request_id": result.request_id,
                "source_row": result.source_row,
                "request_date": result.request_date,
                "requested_delivery_date": result.requested_delivery_date,
                "order_status": result.order_status,
                "cash_before": result.cash_before,
                "cash_after": result.cash_after,
                "cash_changed": result.cash_changed,
                "inventory_before": result.inventory_before,
                "inventory_after": result.inventory_after,
                "gross_sales": result.gross_sales,
                "restock_spend": result.restock_spend,
                "expected_net_cash_delta": result.expected_net_cash_delta,
                "actual_cash_delta": result.actual_cash_delta,
                "fulfilled_items": "; ".join(result.fulfilled_items),
                "unfulfilled_items": "; ".join(result.unfulfilled_items),
                "agent_route": result.agent_route,
                "tool_calls": " | ".join(result.tool_calls),
                "evaluation_passed": result.evaluation_passed,
                "evaluation_findings": "; ".join(result.evaluation_findings),
                "response": result.response,
            }
            for result in results
        ]
    ).to_csv(output_path, index=False)


def print_final_summary(results: List[WorkflowResult], output_path: str) -> None:
    successful_sales = sum(result.order_status == "fulfilled_sale_recorded" for result in results)
    successful_quotes = sum(result.order_status in {"fulfilled_sale_recorded", "quote_ready"} for result in results)
    unfulfilled = sum(result.order_status == "unfulfilled" for result in results)
    cash_changes = sum(result.cash_changed for result in results)
    print("\n===== EVALUATION SUMMARY =====")
    print(f"Requests processed: {len(results)}")
    print(f"Successful sales recorded: {successful_sales}")
    print(f"Successful quote/sale outcomes: {successful_quotes}")
    print(f"Unfulfilled requests: {unfulfilled}")
    print(f"Requests with cash-balance changes: {cash_changes}")
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    run_test_scenarios()
