from pathlib import Path


def test_portfolio_plan_exists() -> None:
    assert Path("docs/portfolio_refactor_plan.md").exists()


def test_remaining_task_briefs_exist() -> None:
    task_docs = sorted(Path("docs/tasks").glob("*.md"))
    done_docs = sorted(Path("docs/done").glob("*.md"))
    assert [doc.name for doc in task_docs] == [
        "14_provider_tests_and_ci.md",
        "15_portfolio_documentation.md",
        "16_polish_and_publish_prep.md",
    ]
    assert [doc.name for doc in done_docs] == [
        "01_bootstrap_repository.md",
        "02_openai_configuration_cleanup.md",
        "03_package_skeleton_and_imports.md",
        "04_data_and_database_layer.md",
        "05_schemas_parsing_and_pricing.md",
        "06_agent_modules.md",
        "07_evaluation_cli.md",
        "08_provider_configuration_contract.md",
        "09_model_factory_and_capability_preflight.md",
        "10_first_class_model_providers.md",
        "11_spicy_replay_dataset.md",
        "12_provider_extensions_and_conformance.md",
        "13_evaluation_model_selection.md",
    ]
