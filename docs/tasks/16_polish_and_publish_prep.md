# Task 16: Polish And Publish Prep

## Goal

Validate and publish the provider-adaptable portfolio repository.

## Scope

- Run formatting, linting, offline tests, the real Ollama workflow, and a sample evaluation.
- Verify package metadata, default dependency size, configuration examples, and legacy deprecation behavior.
- Review tracked files for secrets, local artifacts, model files, generated databases, and oversized files.
- Push the completed main branch to the intended GitHub remote and verify the remote state.
- Add repository topics that reflect multi-agent systems, Pydantic AI, local models, and provider portability.

## Acceptance Criteria

- [ ] The working tree is clean, CI is green, and local Ollama verification passes.
- [ ] README and provider documentation match the shipped configuration and CLI behavior.
- [ ] The intended branch and commit are present on the verified remote without secrets or local model artifacts.

## Verification

- [ ] `python -m pip check`, `ruff check .`, and `pytest --basetemp tmp/pytest -m "not ollama"`
- [ ] `make test-ollama` and one sample local-Ollama evaluation.
- [ ] Verify `git status --short --branch` and the remote branch after push.

## Dependencies

Task 15.

## Files Likely Touched

- `README.md`
- `pyproject.toml`
- `.gitignore`
- `.github/workflows/ci.yml`

## Estimated Scope

Small: validation plus targeted polish; no new architecture.
