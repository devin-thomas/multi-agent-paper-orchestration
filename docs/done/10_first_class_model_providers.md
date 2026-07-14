# Task 10: First-Class Model Providers

## Goal

Ship verified adapters for OpenAI, Anthropic Claude, Google Gemini, and Ollama/local models.

## Scope

- Implement the four first-class adapters through the project-owned factory, reusing Pydantic AI provider implementations where practical.
- Map each provider's credentials, base URL, model identifier, structured-output behavior, and tool capability into the common contract.
- Include all four first-class provider dependencies in the default installation for one-step setup.
- Measure and document the installed dependency impact; do not split extras unless the impact is unexpectedly large and reviewed.
- Provide ready-to-edit TOML profiles with no embedded credentials.

## Acceptance Criteria

- [ ] A default installation can construct all four first-class adapters without additional package extras.
- [ ] Missing credentials or unavailable local endpoints produce provider-specific configuration errors.
- [ ] Provider details do not leak into agent, orchestration, pricing, or database modules.

## Verification

- [ ] Fake-based tests cover construction and capability mapping for all four providers without paid credentials.
- [ ] The existing real Ollama smoke test passes with `gpt-oss:20b`.
- [ ] `python -m pip check`, `pytest --basetemp tmp/pytest`, and `ruff check .` pass.

## Dependencies

Task 09.

## Files Likely Touched

- `src/paper_orchestration/providers/first_class.py`
- `src/paper_orchestration/providers/factory.py`
- `model-providers.toml`
- `pyproject.toml`
- `tests/test_first_class_providers.py`

## Estimated Scope

Medium: 5 files.
