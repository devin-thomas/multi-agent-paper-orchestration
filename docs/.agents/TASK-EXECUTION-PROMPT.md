# Paper Orchestration Task Execution Loop

Use this prompt for one bounded implementation pass through the local refactor task queue. Run it again only after the previous pass has reached a terminal result.

## Prompt

```text
Complete exactly one next executable task for Multi-Agent Paper Orchestration.

Repository: current repository root
Package: src/paper_orchestration/
Preserved behavior reference: legacy/project_starter_passing.py
Task source of truth: numbered briefs in docs/tasks/ and docs/done/
Main plan: docs/portfolio_refactor_plan.md
Target branch: main

Do not ask for a task ID. Read fresh repository state, mechanically choose the one next local task brief, complete only that task, record the result, and stop. This repository does not use GitHub Issues or Linear to choose work; do not infer task status from an external tracker.

Before changing anything:

1. Record the America/Chicago start time.
2. Read every applicable AGENTS.md or CODEX.md instruction file, if present.
3. Read README.md, docs/portfolio_refactor_plan.md, docs/architecture.md, docs/evaluation.md, this prompt, every active task brief in docs/tasks/ in numeric order, and the completed brief or plan note most relevant to the next task.
4. Inspect git status --short --branch, git remote -v, git log -5 --oneline, and the current branch. Treat every already-dirty path as protected: preserve it, do not overwrite or stage it, and do not revert it.
5. Inspect the files, tests, fixtures, and preserved legacy behavior relevant to the candidate task before deciding its implementation details. Read legacy/project_starter_passing.py selectively; it is a behavior reference, not the default edit target.
6. Establish one Python command for the whole pass. If `.venv\\Scripts\\python.exe` exists, use it consistently; otherwise use `python`. Install the project with `<python> -m pip install -e ".[dev]"` before validating a package command such as `python -m paper_orchestration.evaluation`; pytest's configured source path does not prove that the standalone module command is importable. Dependency installation may take time while resolving the declared package versions; wait for its terminal result before diagnosing it as a failure.
7. Create the ignored local pytest parent with `New-Item -ItemType Directory -Force -Path tmp | Out-Null`. Use `<python> -m pytest ... --basetemp tmp\\pytest-<TASK_ID>` for every pytest invocation. The host's default user temp root may be permission-denied, while `tmp/` is intentionally ignored and safe for task-local test artifacts.

Select the task mechanically:

1. A task is complete only when its matching numbered brief is under docs/done/. A brief under docs/tasks/ is incomplete, even if similarly named code or documentation already exists.
2. Sort active briefs by their leading two-digit number. Select the lowest-numbered active brief whose lower-numbered required work is already in docs/done/.
3. Respect explicit dependencies in docs/portfolio_refactor_plan.md. If the lowest-numbered active brief cannot yet run because a stated prerequisite is incomplete, do not skip ahead; report Status: Blocked and name the prerequisite.
4. If no active briefs remain, make no repository changes and report Status: Complete.
5. Read the selected brief in full. Its number and title are TASK_ID for the rest of this pass.
6. Announce the selected TASK_ID and its goal in the chat before implementation begins.

You own TASK_ID only. Do not begin sibling tasks, successors, broader cleanup, publication work, or live evaluation work unless TASK_ID explicitly requires it.

Authority order:

1. TASK_ID goal, scope, and done conditions.
2. The current task sequencing and explicit dependency notes in docs/portfolio_refactor_plan.md.
3. README.md, docs/architecture.md, and docs/evaluation.md for the public project story and technical intent.
4. The preserved legacy implementation for behavior that the task is meant to retain.
5. Existing refactored code and tests as the implementation baseline.

Execution rules:

- Implement the smallest complete vertical slice that satisfies every TASK_ID done condition. Do not add speculative functionality, compatibility shims, unrelated refactors, or work assigned to a later numbered brief.
- Preserve the original datasets, examples, passing output, and legacy source. Add alternate fixtures or generated artifacts only when TASK_ID calls for them; never overwrite baseline evaluation inputs.
- Keep the refactor deterministic at module boundaries. Pydantic-ai agents may interpret language and draft responses, but catalog canonicalization, inventory math, pricing, transaction plans, and response safety require explicit deterministic validation where the architecture calls for it.
- Do not invoke a live OpenAI call or require OPENAI_API_KEY for ordinary tests. Use offline fixtures, fakes, or mocks unless TASK_ID explicitly owns a live evaluation. Never print, commit, or otherwise expose .env values, API keys, databases, logs, caches, or generated local outputs.
- Follow the package layout and conventions already established in src/paper_orchestration/. Keep public names typed and imports clean. Prefer focused, behavior-oriented pytest coverage for changed deterministic behavior.
- When extracting behavior from `legacy/project_starter_passing.py`, preserve it in focused package modules but keep imports side-effect free: defer API-key validation and live agent construction until a runtime entry point creates the agent. Prove pydantic-ai integration offline by faking a framework agent, exercising a registered tool, and asserting that the worker calls `run_sync`.
- Run the narrowest relevant test or lint check after each meaningful implementation slice, then run the complete applicable verification set before completion. The usual baseline is:
  - <python> -m pytest -q --basetemp tmp\\pytest-TASK_ID
  - <python> -m ruff check src scripts tests
  - git diff --check
  Use the Python command selected during preflight; do not mix a system interpreter with a virtual-environment executable.
- Do not delete, reset, checkout, or broadly clean files to make tests pass. Do not modify ignored artifacts to work around a failure. Surface real failures and fix the task-owned cause.
- When TASK_ID is complete, move only its brief from docs/tasks/ to docs/done/ without renaming it. Append a concise completion note to docs/portfolio_refactor_plan.md; do not relocate or rewrite its historical context. Update task-lifecycle tests that intentionally enumerate the active and completed brief sets so the moved brief is reflected.

Completion gate:

Mark TASK_ID complete only when every done condition is implemented, relevant focused tests pass, the full applicable verification set passes, affected documentation is accurate, the brief has moved to docs/done/, the main plan records the completion, and git status contains no accidental secret, cache, database, generated artifact, or unrelated file.

A completed task must have one non-empty task-owned commit. Before committing:

1. Stage only the exact TASK_ID paths; never use git add . or git add -A.
2. Run git diff --cached --check and inspect git diff --cached --name-status plus the staged diff.
3. Verify no protected pre-existing dirty path, credential, local database, cache, generated output, or unrelated change is staged.
4. Commit with a professional subject beginning TASK_ID, for example: Task 05: Extract schemas, parsing, and pricing.
5. Push only when TASK_ID explicitly includes publishing or the user explicitly asks for a push. Task 10 owns general publication preparation and publishing. Do not push another task merely because an origin remote exists.

If a check fails or is skipped, do not claim success. Resolve the task-owned problem when possible; otherwise leave the brief in docs/tasks/, do not create a completion commit, and report Status: Incomplete or Blocked with the exact reason.

At the end:

1. Record the America/Chicago end time and calculate whole minutes worked.
2. Report the exact command results, including any failed or skipped checks.
3. If the completion gate passed, commit the exact task-owned changes before declaring TASK_ID complete.
4. Stop. Do not start another task.

Report using this structure:

Task: TASK_ID — <title, or None>
Status: Complete | Incomplete | Blocked
Start: <America/Chicago timestamp>
End: <America/Chicago timestamp>
Minutes worked: <whole number>
Commit: <SHA and subject, or Not created>

Implemented:
- <outcomes or None>

Validation:
- <exact command>: <result>

Changed files:
- <paths or None>

Task lifecycle:
- <brief moved to docs/done/ and plan note added, or exact reason it remains active>

Failures, skipped checks, or residual risks:
- None
  OR
- FAILED/SKIPPED/BLOCKED: <clear explanation>

Do not start another task after reporting.
```

## Selection Invariant

No task is hard-coded in this prompt. Resolve the next task from the current numbered brief locations on every run, preserve work already in progress, and stop after one task-level result.
