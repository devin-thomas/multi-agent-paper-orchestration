from pathlib import Path


def test_portfolio_plan_exists() -> None:
    assert Path("docs/portfolio_refactor_plan.md").exists()


def test_ten_task_briefs_exist() -> None:
    task_docs = sorted(Path("docs/tasks").glob("*.md"))
    assert len(task_docs) == 10

