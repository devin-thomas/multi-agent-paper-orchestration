# Task 13: Evaluation Model Selection

## Goal

Expose simple global model selection in the evaluation CLI while keeping advanced role overrides in TOML.

## Scope

- Add `--profile` and optional `--model` arguments as the only model-related CLI overrides.
- Apply `--model` only to the global default; do not add CLI credentials, headers, endpoints, or per-agent maps.
- Validate the effective configuration and capability contract before initializing the evaluation database.
- Record the effective profile, global model, and per-agent resolved models in evaluation metadata without secrets.
- Preserve existing input, output, database, sleep, and reset behavior.

## Acceptance Criteria

- [ ] A user can switch between configured OpenAI, Claude, Gemini, and Ollama profiles with one flag.
- [ ] Advanced per-agent overrides come only from TOML and remain visible in secret-free evaluation metadata.
- [ ] Invalid selections fail before files, databases, or paid model calls are created.

## Verification

- [ ] Parser and runner tests cover profile selection, global model override, metadata, and early failure.
- [ ] Run one sample evaluation using the local Ollama profile.
- [ ] `pytest --basetemp tmp/pytest` and `ruff check .` pass.

## Dependencies

Tasks 08 through 10.

## Files Likely Touched

- `src/paper_orchestration/evaluation.py`
- `src/paper_orchestration/config.py`
- `src/paper_orchestration/schemas.py`
- `tests/test_evaluation.py`

## Estimated Scope

Medium: 4 files.
