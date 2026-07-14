"""SQLite-backed inventory, transaction, finance, and quote-history helpers."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .catalog import ITEM_BY_NAME, paper_supplies
from .config import load_settings

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = _REPOSITORY_ROOT / "data"


def _database_path(database_path: Path | str | None = None) -> Path:
    if database_path is not None:
        return Path(database_path)
    try:
        return load_settings().database_path
    except RuntimeError:
        return Path("outputs/munder_difflin.db")


def get_connection(database_path: Path | str | None = None) -> sqlite3.Connection:
    """Open the configured SQLite database, creating its parent directory."""
    path = _database_path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path)


def generate_sample_inventory(
    supplies: list[dict], coverage: float = 0.4, seed: int = 137
) -> pd.DataFrame:
    """Generate reproducible starting inventory for a subset of the catalog."""
    rng = np.random.default_rng(seed)
    count = int(len(supplies) * coverage)
    selected_indices = rng.choice(len(supplies), size=count, replace=False)
    return pd.DataFrame(
        [
            {
                "item_name": supplies[index]["item_name"],
                "category": supplies[index]["category"],
                "unit_price": supplies[index]["unit_price"],
                "current_stock": int(rng.integers(200, 800)),
                "min_stock_level": int(rng.integers(50, 150)),
            }
            for index in selected_indices
        ]
    )


def init_database(
    seed: int = 137,
    database_path: Path | str | None = None,
    data_dir: Path | str | None = None,
) -> None:
    """Create the local database with inventory and request-history tables."""
    data_path = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    request_path = data_path / "quote_requests.csv"
    if not request_path.exists():
        raise FileNotFoundError(f"Quote request data not found: {request_path}")

    inventory_df = generate_sample_inventory(paper_supplies, seed=seed)
    quote_requests_df = pd.read_csv(request_path)
    quote_requests_df.insert(0, "id", range(1, len(quote_requests_df) + 1))

    with get_connection(database_path) as conn:
        pd.DataFrame(
            columns=["id", "item_name", "transaction_type", "units", "price", "transaction_date"]
        ).to_sql("transactions", conn, if_exists="replace", index=False)
        quote_requests_df.to_sql("quote_requests", conn, if_exists="replace", index=False)
        pd.DataFrame(
            columns=[
                "request_id",
                "total_amount",
                "quote_explanation",
                "job_type",
                "order_size",
                "event_type",
                "order_date",
            ]
        ).to_sql("quotes", conn, if_exists="replace", index=False)
        inventory_df.to_sql("inventory", conn, if_exists="replace", index=False)

        initial_date = datetime(2025, 1, 1).isoformat()
        initial_transactions = [
            (None, "sales", None, 50000.0, initial_date),
            *[
                (
                    row.item_name,
                    "stock_orders",
                    int(row.current_stock),
                    float(row.current_stock * row.unit_price),
                    initial_date,
                )
                for row in inventory_df.itertuples()
            ],
        ]
        conn.executemany(
            """
            INSERT INTO transactions
                (item_name, transaction_type, units, price, transaction_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            initial_transactions,
        )


def ensure_inventory_reference(item_name: str, database_path: Path | str | None = None) -> None:
    if item_name not in ITEM_BY_NAME:
        return
    with get_connection(database_path) as conn:
        existing = conn.execute(
            "SELECT 1 FROM inventory WHERE item_name = ?", (item_name,)
        ).fetchone()
        if existing is None:
            item = ITEM_BY_NAME[item_name]
            conn.execute(
                """
                INSERT INTO inventory
                    (item_name, category, unit_price, current_stock, min_stock_level)
                VALUES (?, ?, ?, ?, ?)
                """,
                (item["item_name"], item["category"], item["unit_price"], 0, 100),
            )


def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: str | datetime,
    database_path: Path | str | None = None,
) -> int:
    """Record a stock order or sale transaction."""
    if transaction_type not in {"stock_orders", "sales"}:
        raise ValueError("Transaction type must be 'stock_orders' or 'sales'")
    if quantity <= 0:
        raise ValueError("Quantity must be positive")
    if item_name:
        ensure_inventory_reference(item_name, database_path)
    date_str = date.isoformat() if isinstance(date, datetime) else date
    with get_connection(database_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO transactions (item_name, transaction_type, units, price, transaction_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (item_name, transaction_type, quantity, price, date_str),
        )
        return int(cursor.lastrowid)


def get_all_inventory(as_of_date: str, database_path: Path | str | None = None) -> dict[str, int]:
    """Return positive stock levels as of a date."""
    query = """
        SELECT item_name, SUM(CASE
            WHEN transaction_type = 'stock_orders' THEN units
            WHEN transaction_type = 'sales' THEN -units
            ELSE 0 END) AS stock
        FROM transactions
        WHERE item_name IS NOT NULL AND transaction_date <= ?
        GROUP BY item_name HAVING stock > 0
    """
    with get_connection(database_path) as conn:
        result = pd.read_sql_query(query, conn, params=(as_of_date,))
    return dict(zip(result["item_name"], result["stock"].astype(int), strict=True))


def get_stock_level(
    item_name: str,
    as_of_date: str | datetime,
    database_path: Path | str | None = None,
) -> pd.DataFrame:
    """Return stock level for one item as of a date."""
    date_str = as_of_date.isoformat() if isinstance(as_of_date, datetime) else as_of_date
    query = """
        SELECT ? AS item_name, COALESCE(SUM(CASE
            WHEN transaction_type = 'stock_orders' THEN units
            WHEN transaction_type = 'sales' THEN -units
            ELSE 0 END), 0) AS current_stock
        FROM transactions WHERE item_name = ? AND transaction_date <= ?
    """
    with get_connection(database_path) as conn:
        return pd.read_sql_query(query, conn, params=(item_name, item_name, date_str))


def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """Estimate supplier delivery date from order date and quantity."""
    base_date = datetime.fromisoformat(input_date_str.split("T")[0])
    days = 0 if quantity <= 10 else 1 if quantity <= 100 else 4 if quantity <= 1000 else 7
    return (base_date + timedelta(days=days)).strftime("%Y-%m-%d")


def get_cash_balance(as_of_date: str | datetime, database_path: Path | str | None = None) -> float:
    """Calculate cash balance as of a date."""
    date_str = as_of_date.isoformat() if isinstance(as_of_date, datetime) else as_of_date
    with get_connection(database_path) as conn:
        transactions = pd.read_sql_query(
            "SELECT * FROM transactions WHERE transaction_date <= ?", conn, params=(date_str,)
        )
    prices = pd.to_numeric(transactions["price"], errors="raise")
    sales = prices.loc[transactions["transaction_type"] == "sales"].sum()
    purchases = prices.loc[transactions["transaction_type"] == "stock_orders"].sum()
    return float(sales - purchases)


def get_stock_quantity(
    item_name: str, as_of_date: str, database_path: Path | str | None = None
) -> int:
    stock_df = get_stock_level(item_name, as_of_date, database_path)
    return int(stock_df.iloc[0]["current_stock"] or 0) if not stock_df.empty else 0


def generate_financial_report(
    as_of_date: str | datetime, database_path: Path | str | None = None
) -> dict:
    """Generate cash, inventory, and total asset values."""
    date_str = as_of_date.isoformat() if isinstance(as_of_date, datetime) else as_of_date
    cash = get_cash_balance(date_str, database_path)
    with get_connection(database_path) as conn:
        inventory_df = pd.read_sql_query("SELECT * FROM inventory", conn)
    inventory_summary = []
    inventory_value = 0.0
    for item in inventory_df.itertuples():
        stock = get_stock_quantity(item.item_name, date_str, database_path)
        value = float(stock * item.unit_price)
        inventory_value += value
        inventory_summary.append(
            {
                "item_name": item.item_name,
                "stock": stock,
                "unit_price": float(item.unit_price),
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


def search_quote_history(
    search_terms: list[str], limit: int = 5, database_path: Path | str | None = None
) -> list[dict]:
    """Search historical quotes for comparable prior requests."""
    conditions = []
    params: list[str | int] = []
    for term in search_terms:
        conditions.append("(LOWER(qr.response) LIKE ? OR LOWER(q.quote_explanation) LIKE ?)")
        params.extend([f"%{term.lower()}%", f"%{term.lower()}%"])  # noqa: PERF401
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    query = f"""
        SELECT qr.response AS original_request, q.total_amount, q.quote_explanation,
               q.job_type, q.order_size, q.event_type, q.order_date
        FROM quotes q JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause} ORDER BY q.order_date DESC LIMIT ?
    """
    params.append(limit)
    with get_connection(database_path) as conn:
        result = conn.execute(query, params)
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]
