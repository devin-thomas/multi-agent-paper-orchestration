# Beaver's Choice Portfolio Refactor Plan

## Current Starting Point

- `repo` is present but empty/uninitialized from the local shell view.
- `submission/project_starter.py` is the passing source of truth: 1,761 lines, five framework-executed pydantic-ai agents, SQLite helper functions, deterministic validation, evaluation runner, and CSV output.
- The passing run processed 20 requests: 5 fulfilled sales, 5 quote-ready outcomes, 7 partial quotes, 3 unfulfilled requests, 5 cash-changing requests, $1,413.50 gross sales, $628.23 restock spend, and $785.27 net cash change.
- The original capstone constraints required a single Python file. The portfolio repo should intentionally move beyond that constraint while preserving a single-file legacy artifact if useful.
- Vocareum coupling is limited and easy to remove:
  - `UDACITY_OPENAI_API_KEY`
  - forced `OPENAI_BASE_URL=https://openai.vocareum.com/v1`
  - runtime error mentioning `UDACITY_OPENAI_API_KEY`

## Recommended Portfolio Goals

1. Make the project read as a polished applied AI engineering case study: "multi-agent sales and inventory orchestration for a paper supplier."
2. Preserve the course-aligned strengths: orchestrator-workers, routing, structured Pydantic outputs, tool use, SQLite database interaction, state coordination, deterministic validation, and evaluation.
3. Refactor lightly: split the monolith by responsibility without redesigning the working system.
4. Convert to normal OpenAI configuration: use `OPENAI_API_KEY`, optional `OPENAI_MODEL`, optional `.env`, and no Vocareum base URL by default.
5. Make local reproduction simple: `make install`, `make test`, `make evaluate`, and one clear CLI command.
6. Add hiring-manager-friendly evidence: architecture diagram, sample outputs, evaluation summary, design tradeoffs, and test coverage.
7. Keep the repository honest about limitations: stochastic LLM behavior, cost, SQLite/local scope, and opportunities for future production hardening.

## Proposed Package Layout

```text
multi-agent-paper-orchestration/
├── .github/workflows/ci.yml
├── data/
│   ├── quote_requests.csv
│   └── quote_requests_sample.csv
├── docs/
│   ├── architecture.md
│   ├── evaluation.md
│   └── beavers_choice_workflow.mmd
├── examples/
│   ├── sample_customer_requests.md
│   └── sample_outputs.md
├── scripts/
│   └── run_evaluation.py
├── src/
│   └── paper_orchestration/
│       ├── __init__.py
│       ├── config.py
│       ├── catalog.py
│       ├── database.py
│       ├── schemas.py
│       ├── parsing.py
│       ├── pricing.py
│       ├── tools.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── intake.py
│       │   ├── inventory.py
│       │   ├── quoting.py
│       │   ├── sales.py
│       │   └── orchestrator.py
│       └── evaluation.py
├── tests/
│   ├── test_parsing.py
│   ├── test_pricing.py
│   ├── test_inventory_validation.py
│   ├── test_sales_plan.py
│   └── test_response_quality.py
├── .env.example
├── .gitignore
├── LICENSE.md
├── Makefile
├── pyproject.toml
└── README.md
```

## Refactor Boundaries

- `config.py`: environment loading, model name, paths, database path. Normal OpenAI only.
- `catalog.py`: static catalog and lookup maps.
- `database.py`: SQLite connection, initialization, inventory, transactions, cash balance, financial report, quote history.
- `schemas.py`: all Pydantic models and dataclasses.
- `parsing.py`: request text cleanup, item extraction, delivery-date parsing, catalog resolution.
- `pricing.py`: unit price, wholesale cost, discount rules.
- `tools.py`: tool-adjacent helper wrappers where shared by agents.
- `agents/base.py`: `make_framework_agent`, pydantic-ai API compatibility, output extraction, tool audit recorder.
- `agents/intake.py`, `inventory.py`, `quoting.py`, `sales.py`: one worker agent per module.
- `agents/orchestrator.py`: route planning, deterministic validation, final response, response quality checks.
- `evaluation.py`: test scenario runner, result CSV writer, summary metrics.

## README Story

Use the NASA RAG README style:

1. One-sentence value proposition.
2. Short "How it works" section with Mermaid architecture.
3. Quick start with `OPENAI_API_KEY`, not `UDACITY_OPENAI_API_KEY`.
4. Make shortcuts.
5. Evaluation results table.
6. Project structure.
7. Design notes and limits.
8. Data/license note explaining Udacity starter data and educational origin.

Suggested headline:

> Multi-agent paper sales orchestration system using pydantic-ai, SQLite-backed tools, structured outputs, deterministic validation, and reproducible evaluation.

## Small Tasks

1. **Bootstrap Repository**
   - Initialize `repo`, copy passing submission inputs, add `.gitignore`, `.env.example`, `LICENSE.md`, `pyproject.toml`, `Makefile`, and starter README.
   - Set remote target later after GitHub repo exists: `git@github.com:devin-thomas/multi-agent-paper-orchestration`.

2. **OpenAI Configuration Cleanup**
   - Replace `UDACITY_OPENAI_API_KEY` and forced Vocareum base URL with `OPENAI_API_KEY`.
   - Add `OPENAI_MODEL`/`BEAVERS_CHOICE_AGENT_MODEL` compatibility if useful.
   - Document `.env` usage and make missing-key errors clear.

3. **Package Skeleton And Imports**
   - Create `src/paper_orchestration`.
   - Move code into modules without changing behavior.
   - Keep import paths clean and avoid broad redesign.

4. **Data And Database Layer**
   - Move catalog, CSV loading, SQLite initialization, inventory, transaction, financial-report, and quote-history helpers into stable modules.
   - Add deterministic tests around inventory snapshots, cash balance, and transaction behavior.

5. **Schemas, Parsing, And Pricing**
   - Move Pydantic models, text parsing, catalog canonicalization, and pricing rules into dedicated modules.
   - Add offline tests for edge cases: A4/copy paper, unknown items, dates, quantity consolidation, discounts.

6. **Agent Modules**
   - Split Intake, Inventory, Quoting, Sales, and Orchestrator agents into separate files.
   - Preserve pydantic-ai tool registration and framework-executed `run_sync` calls.
   - Keep deterministic validation in the orchestrator as an explicit production-quality guardrail.

7. **Evaluation CLI**
   - Convert `run_test_scenarios` into `python -m paper_orchestration.evaluation` or `scripts/run_evaluation.py`.
   - Support input/output paths, DB reset path, optional sleep, and artifact directory.
   - Preserve the current metrics and CSV columns.

8. **Tests And CI**
   - Add pytest tests for deterministic modules first.
   - Add an LLM-light smoke test that uses fakes/mocks, not live OpenAI calls.
   - Add GitHub Actions for `ruff` and `pytest`.

9. **Portfolio Documentation**
   - Write README, `docs/architecture.md`, `docs/evaluation.md`, Mermaid diagram, and sample output snippets.
   - Emphasize syllabus skills: routing, parallelization opportunities, structured outputs, tool use, database interaction, state coordination, evaluation.

10. **Polish, GitHub Publish Prep**
   - Run formatting, linting, tests, and evaluation.
   - Confirm no database artifacts, secrets, logs, or bulky generated files are committed unless intentionally placed under `examples/` or `docs/`.
   - After the remote repo is created, set remote, push, and optionally add repo topics.

## Parallelization Plan

- Tasks 1 and 2 should happen first because every other branch depends on repo shape and environment configuration.
- After Task 3 creates the package skeleton, these can run in parallel:
  - Task 4: data/database layer
  - Task 5: schemas/parsing/pricing
  - Task 9: documentation draft using current behavior and diagram
- Task 6 depends on Tasks 4 and 5.
- Task 7 depends on Task 6 enough to call the package, but CSV/report polishing can start earlier.
- Task 8 can start as soon as Tasks 4 and 5 expose importable modules.
- Task 10 is last.

## Suggested First Implementation Slice

Do Tasks 1-2 plus a minimal Task 3:

- Initialize the repo.
- Copy `quote_requests.csv`, `quote_requests_sample.csv`, and the passing `project_starter.py` as `legacy/project_starter_passing.py`.
- Create `src/paper_orchestration/config.py`.
- Remove Vocareum assumptions in the working entrypoint.
- Add `.env.example`, `pyproject.toml`, `Makefile`, and a README scaffold.

This gives us a clean portfolio shell and a reversible baseline before the larger module split.
