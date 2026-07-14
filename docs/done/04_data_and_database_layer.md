# Task 04: Data And Database Layer

## Goal

Isolate catalog data, SQLite initialization, inventory queries, transactions, cash balance, financial reports, and quote history.

## Scope

- Move catalog constants into `catalog.py`.
- Move connection and database helpers into `database.py`.
- Keep database path configurable.
- Preserve the helper functions required by the capstone rubric:
  - `create_transaction`
  - `get_all_inventory`
  - `get_stock_level`
  - `get_supplier_delivery_date`
  - `get_cash_balance`
  - `generate_financial_report`
  - `search_quote_history`

## Done When

- Database helpers can be tested without running live LLM agents.
- Generated databases stay out of Git.
- Function names remain stable for agent tool registration.

