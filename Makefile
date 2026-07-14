.PHONY: install test test-ollama lint format plan

install:
	python -m pip install -e ".[dev]"

test:
	pytest --basetemp tmp/pytest

test-ollama:
	pytest --basetemp tmp/pytest -m ollama -rs

lint:
	ruff check .

format:
	ruff format .

plan:
	python -c "from pathlib import Path; print(Path('docs/portfolio_refactor_plan.md').read_text())"

