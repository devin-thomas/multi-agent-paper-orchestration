from datetime import datetime

from paper_orchestration.database import (
    create_transaction,
    generate_financial_report,
    get_cash_balance,
    get_stock_level,
    get_supplier_delivery_date,
    init_database,
    search_quote_history,
)


def test_database_helpers_track_inventory_cash_and_reports(tmp_path) -> None:
    database_path = tmp_path / "test.db"
    init_database(database_path=database_path)

    before = get_stock_level("A4 paper", "2025-01-01T00:00:00", database_path)
    starting_stock = int(before.iloc[0]["current_stock"])

    create_transaction("A4 paper", "stock_orders", 20, 1.0, datetime(2025, 1, 2), database_path)
    create_transaction("A4 paper", "sales", 5, 2.0, "2025-01-03T00:00:00", database_path)

    stock = get_stock_level("A4 paper", "2025-01-03T00:00:00", database_path)
    assert int(stock.iloc[0]["current_stock"]) == starting_stock + 15
    assert get_cash_balance("2025-01-03T00:00:00", database_path) < 50000
    report = generate_financial_report("2025-01-03T00:00:00", database_path)
    assert report["total_assets"] == report["cash_balance"] + report["inventory_value"]


def test_supplier_dates_and_empty_quote_history_are_deterministic(tmp_path) -> None:
    database_path = tmp_path / "test.db"
    init_database(database_path=database_path)

    assert get_supplier_delivery_date("2025-01-01", 10) == "2025-01-01"
    assert get_supplier_delivery_date("2025-01-01", 1001) == "2025-01-08"
    assert search_quote_history(["paper"], database_path=database_path) == []
