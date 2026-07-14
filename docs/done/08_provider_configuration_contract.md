# Task 08: Provider Configuration Contract

## Goal

Replace the OpenAI-shaped runtime settings with a provider-neutral, typed configuration contract.

## Scope

- Add a versioned TOML configuration file with named provider profiles, one global default, and optional per-agent overrides.
- Keep secrets out of TOML; profiles may name environment variables that contain credentials.
- Preserve `OPENAI_API_KEY`, `OPENAI_MODEL`, and `BEAVERS_CHOICE_AGENT_MODEL` as legacy fallbacks and emit a targeted deprecation warning only when legacy-only configuration is used.
- Define precedence explicitly: advanced per-agent override, global profile/model selection, then legacy fallback.
- Keep the pre-task Ollama behavior working while moving it behind the new contract.

## Acceptance Criteria

- [ ] Typed settings load OpenAI, Anthropic, Gemini, and Ollama profile shapes without importing agent modules.
- [ ] Configuration errors identify the profile and missing or invalid field without exposing secret values.
- [ ] Existing OpenAI-only and local Ollama setups continue to load through documented migration paths.

## Verification

- [ ] `pytest --basetemp tmp/pytest tests/test_model_configuration.py`
- [ ] Tests cover TOML, environment-secret references, precedence, and legacy warnings.
- [ ] `ruff check .`

## Dependencies

Task 07. Task 11 is already complete and is unrelated.

## Files Likely Touched

- `src/paper_orchestration/config.py`
- `model-providers.toml`
- `.env.example`
- `tests/test_model_configuration.py`

## Estimated Scope

Medium: 4 files.
