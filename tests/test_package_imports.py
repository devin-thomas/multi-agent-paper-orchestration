import importlib


def test_package_modules_import_cleanly() -> None:
    modules = [
        "paper_orchestration.config",
        "paper_orchestration.catalog",
        "paper_orchestration.database",
        "paper_orchestration.schemas",
        "paper_orchestration.parsing",
        "paper_orchestration.pricing",
        "paper_orchestration.tools",
        "paper_orchestration.evaluation",
        "paper_orchestration.agents.base",
        "paper_orchestration.agents.intake",
        "paper_orchestration.agents.inventory",
        "paper_orchestration.agents.quoting",
        "paper_orchestration.agents.sales",
        "paper_orchestration.agents.orchestrator",
    ]

    for module in modules:
        assert importlib.import_module(module) is not None
