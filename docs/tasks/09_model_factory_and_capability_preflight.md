# Task 09: Model Factory And Capability Preflight

## Goal

Make every agent depend on a project-owned model factory and reject incompatible models before workflow execution.

## Scope

- Define project-owned adapter, factory, capability, and compatibility-error contracts around Pydantic AI.
- Resolve the global model by default and allow configuration-only model/profile overrides for each of the five agent roles.
- Require structured output and tool calling for roles that use them; an adapter may satisfy a capability natively or through validated emulation.
- Run capability preflight before database mutation or any model request.
- Replace direct model-string construction in `agents/base.py` with the resolved factory result.

## Acceptance Criteria

- [ ] All five agents obtain models through one project-owned boundary.
- [ ] An incompatible model fails early with a precise provider, model, role, and missing-capability message.
- [ ] No code path silently downgrades structured output, tool use, or deterministic business validation.

## Verification

- [ ] Contract tests prove global defaults and per-agent overrides resolve correctly.
- [ ] Tests prove preflight happens before an agent or database side effect.
- [ ] `pytest --basetemp tmp/pytest` and `ruff check .` pass.

## Dependencies

Task 08.

## Files Likely Touched

- `src/paper_orchestration/providers/base.py`
- `src/paper_orchestration/providers/factory.py`
- `src/paper_orchestration/agents/base.py`
- `src/paper_orchestration/config.py`
- `tests/test_model_factory.py`

## Estimated Scope

Medium: 5 files.
