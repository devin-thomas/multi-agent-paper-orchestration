# Task 14: Provider Tests And CI

## Goal

Create a credible provider test matrix without requiring paid credentials in CI.

## Scope

- Keep deterministic tests and fake-based provider contract tests in the default CI job.
- Expand the marked Ollama suite from the current intake smoke test to a small end-to-end workflow covering all five roles, structured outputs, tool calls, and capability preflight.
- Run Ollama tests automatically during local `make test` when the configured model is available; retain `make test-ollama` for focused runs.
- Exclude live Ollama tests explicitly in hosted CI unless a self-hosted Ollama runner is configured.
- Add Ruff and pytest GitHub Actions checks.

## Acceptance Criteria

- [ ] Hosted CI passes with fakes and no provider credentials.
- [ ] A local `gpt-oss:20b` run covers the complete workflow and fails clearly when capabilities are insufficient.
- [ ] No test silently passes by replacing a requested live provider with a fake.

## Verification

- [ ] `pytest --basetemp tmp/pytest -m "not ollama"`
- [ ] `make test-ollama`
- [ ] `ruff check .` and the GitHub Actions workflow both pass.

## Dependencies

Tasks 10, 12, and 13.

## Files Likely Touched

- `tests/test_ollama_integration.py`
- `tests/test_provider_conformance.py`
- `.github/workflows/ci.yml`
- `Makefile`

## Estimated Scope

Medium: 4 files.
