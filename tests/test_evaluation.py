from pathlib import Path

import pandas as pd

from paper_orchestration.evaluation import (
    RESULT_COLUMNS,
    load_requests,
    run_evaluation,
    write_results_csv,
)
from paper_orchestration.schemas import WorkflowResult


def _workflow_result(request_id: int, source_row: int) -> WorkflowResult:
    return WorkflowResult(
        request_id=request_id,
        source_row=source_row,
        request_date="2025-04-01",
        requested_delivery_date="2025-04-15",
        order_status="quote_ready",
        response="A quote is ready because the requested item is available.",
        cash_before=10.0,
        cash_after=10.0,
        inventory_before=20.0,
        inventory_after=20.0,
        fulfilled_items=["A4 paper"],
        agent_route="IntakeAgent -> OrchestratorAgent",
        tool_calls=["IntakeAgent.extract_line_items: request parsed"],
        evaluation_passed=True,
    )


def test_load_requests_assigns_stable_dates_when_fixture_omits_them(tmp_path: Path) -> None:
    input_path = tmp_path / "requests.csv"
    input_path.write_text("request\nfirst request\nsecond request\n", encoding="utf-8")

    requests = load_requests(input_path)

    assert requests["_source_row"].tolist() == [1, 2]
    assert requests["request_date"].dt.strftime("%Y-%m-%d").tolist() == ["2025-04-01", "2025-04-02"]


def test_write_results_csv_preserves_audit_columns(tmp_path: Path) -> None:
    output_path = tmp_path / "artifacts" / "results.csv"

    write_results_csv([_workflow_result(1, 1)], output_path)

    results = pd.read_csv(output_path)
    assert results.columns.tolist() == RESULT_COLUMNS
    assert results.loc[0, "agent_route"] == "IntakeAgent -> OrchestratorAgent"
    assert results.loc[0, "evaluation_passed"]


def test_run_evaluation_uses_requested_paths_and_prints_summary(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    input_path = tmp_path / "requests.csv"
    input_path.write_text("request\nfirst request\n", encoding="utf-8")
    output_path = tmp_path / "results.csv"
    database_path = tmp_path / "evaluation.db"
    initialized_paths: list[Path] = []

    class FakeOrchestrator:
        def process_request(
            self, request_id: int, source_row: int, row: pd.Series
        ) -> WorkflowResult:
            assert row["request"] == "first request"
            return _workflow_result(request_id, source_row)

    monkeypatch.setattr(
        "paper_orchestration.evaluation.init_database",
        lambda database_path: initialized_paths.append(database_path),
    )
    monkeypatch.setattr(
        "paper_orchestration.evaluation.build_agent_team",
        FakeOrchestrator,
    )

    results = run_evaluation(input_path, output_path, database_path)

    assert initialized_paths == [database_path]
    assert [result.source_row for result in results] == [1]
    assert output_path.exists()
    assert "Evaluation complete" in capsys.readouterr().out
