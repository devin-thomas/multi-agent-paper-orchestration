# Task 08: Tests And CI

## Goal

Add enough test coverage and automation to make the refactor credible without requiring expensive live LLM calls in CI.

## Scope

- Add pytest tests for deterministic parsing, pricing, inventory validation, transaction planning, and response quality checks.
- Use fakes or mocks for LLM-facing smoke tests.
- Add Ruff linting.
- Keep GitHub Actions lightweight.

## Done When

- `pytest` passes locally without an OpenAI API key.
- `ruff check .` passes.
- CI runs lint and tests on push and pull request.

