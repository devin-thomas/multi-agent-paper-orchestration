.PHONY: install test lint format plan

install:
	python -m pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

plan:
	python -c "from pathlib import Path; print(Path('docs/portfolio_refactor_plan.md').read_text())"

