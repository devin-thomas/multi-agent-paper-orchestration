# Task 07: Evaluation CLI

## Goal

Turn the evaluation runner into a reusable CLI that can regenerate the project evidence.

## Scope

- Add `python -m paper_orchestration.evaluation` or finish `scripts/run_evaluation.py`.
- Support configurable input path, output path, database path, sleep interval, and reset behavior.
- Preserve the passing CSV columns where practical.
- Print a concise final summary.

## Done When

- A fresh user can run one documented command and produce an evaluation CSV.
- The output captures agent route, tool calls, status, financial changes, and response quality.

