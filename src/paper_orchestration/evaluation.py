"""Reusable evaluation runner for the framework-executed paper-agent workflow."""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import pandas as pd

from .agents.orchestrator import build_agent_team
from .database import init_database
from .schemas import WorkflowResult

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = REPOSITORY_ROOT / "data" / "quote_requests_sample.csv"
DEFAULT_ARTIFACT_DIR = REPOSITORY_ROOT / "outputs"
RESULT_COLUMNS = [
    "request_id",
    "source_row",
    "request_date",
    "requested_delivery_date",
    "order_status",
    "cash_before",
    "cash_after",
    "cash_changed",
    "inventory_before",
    "inventory_after",
    "gross_sales",
    "restock_spend",
    "expected_net_cash_delta",
    "actual_cash_delta",
    "fulfilled_items",
    "unfulfilled_items",
    "agent_route",
    "tool_calls",
    "evaluation_passed",
    "evaluation_findings",
    "response",
]


def load_requests(input_path: Path) -> pd.DataFrame:
    """Load requests in a stable order, assigning dates for the preserved fixture when needed."""
    requests = pd.read_csv(input_path)
    if "request" not in requests:
        raise ValueError(f"Evaluation input must contain a 'request' column: {input_path}")

    requests["_source_row"] = range(1, len(requests) + 1)
    if "request_date" not in requests:
        requests["request_date"] = pd.date_range("2025-04-01", periods=len(requests), freq="D")
    else:
        requests["request_date"] = pd.to_datetime(requests["request_date"], errors="raise")

    return requests.sort_values(["request_date", "_source_row"], kind="mergesort").reset_index(
        drop=True
    )


def write_results_csv(results: list[WorkflowResult], output_path: Path) -> None:
    """Write the audit columns preserved from the passing evaluation artifact."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
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
    pd.DataFrame(rows, columns=RESULT_COLUMNS).to_csv(output_path, index=False)


def print_final_summary(results: list[WorkflowResult], output_path: Path) -> None:
    """Print concise outcome counts and the generated artifact location."""
    sales = sum(result.order_status == "fulfilled_sale_recorded" for result in results)
    quote_ready = sum(result.order_status == "quote_ready" for result in results)
    unfulfilled = sum(result.order_status == "unfulfilled" for result in results)
    cash_changes = sum(result.cash_changed for result in results)
    print("Evaluation complete")
    print(f"Requests processed: {len(results)}")
    print(f"Fulfilled sales: {sales}; quote-ready: {quote_ready}; unfulfilled: {unfulfilled}")
    print(f"Cash-changing requests: {cash_changes}")
    print(f"Results: {output_path}")


def run_evaluation(
    input_path: Path,
    output_path: Path,
    database_path: Path,
    sleep_seconds: float = 0.0,
    reset_database: bool = False,
) -> list[WorkflowResult]:
    """Run the agent workflow over one CSV fixture and write its audit artifact."""
    if sleep_seconds < 0:
        raise ValueError("sleep_seconds must be non-negative")

    requests = load_requests(input_path)
    if reset_database or not database_path.exists():
        init_database(database_path=database_path)

    # Agent tools use the configured default database path; the runner passes it explicitly.
    os.environ["BEAVERS_CHOICE_DB_PATH"] = str(database_path)
    orchestrator = build_agent_team()
    results: list[WorkflowResult] = []

    for request_id, (_, row) in enumerate(requests.iterrows(), start=1):
        result = orchestrator.process_request(request_id, int(row["_source_row"]), row)
        results.append(result)
        if sleep_seconds:
            time.sleep(sleep_seconds)

    write_results_csv(results, output_path)
    print_final_summary(results, output_path)
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate the paper-orchestration agent workflow.")
    parser.add_argument(
        "--input", type=Path, default=DEFAULT_INPUT_PATH, help="Request CSV to evaluate."
    )
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument(
        "--output", type=Path, help="CSV result path; defaults under --artifact-dir."
    )
    parser.add_argument(
        "--database", type=Path, help="SQLite database path; defaults under --artifact-dir."
    )
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--reset-database", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_path = args.output or args.artifact_dir / "evaluation_results.csv"
    database_path = args.database or args.artifact_dir / "munder_difflin.db"
    run_evaluation(
        input_path=args.input,
        output_path=output_path,
        database_path=database_path,
        sleep_seconds=args.sleep_seconds,
        reset_database=args.reset_database,
    )


if __name__ == "__main__":
    main()
