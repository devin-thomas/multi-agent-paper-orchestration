# Task 06: Agent Modules

## Goal

Split the five pydantic-ai agents into separate modules while preserving framework-executed behavior.

## Scope

- Move shared agent utilities into `agents/base.py`.
- Move workers into:
  - `agents/intake.py`
  - `agents/inventory.py`
  - `agents/quoting.py`
  - `agents/sales.py`
  - `agents/orchestrator.py`
- Preserve tool registration with pydantic-ai decorators.
- Preserve `run_sync` execution through framework agents.
- Keep deterministic validation in the orchestrator.

## Done When

- Each agent has one clear module and responsibility.
- Tool audit output still identifies agent and tool names.
- The prior reviewer concern is visibly addressed: framework agents are executed, not merely used as tool registries.

