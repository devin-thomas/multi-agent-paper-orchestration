# Task 15: Portfolio Documentation

## Goal

Explain the multi-provider architecture and make every first-class setup reproducible.

## Scope

- Expand the README with the problem statement, architecture, quick start, evaluation evidence, and model portability story.
- Document OpenAI, Claude, Gemini, and Ollama profile setup with secret-safe examples.
- Explain global defaults, advanced per-agent overrides, CLI profile/model selection, capability preflight, and extension support.
- Update architecture and evaluation docs, including the fake-CI versus real-local-Ollama test boundary.
- Add curated output examples and honest limitations around model variance, cost, privacy, latency, and local hardware.

## Acceptance Criteria

- [ ] A new user can select any first-class provider without reading source code.
- [ ] A technical reviewer can distinguish first-class support from extension compatibility and understand failure behavior.
- [ ] Every documented command and file path matches the repository.

## Verification

- [ ] Run each non-paid quick-start and test command from the repository root.
- [ ] Check all internal Markdown links and Mermaid rendering.
- [ ] Confirm no example contains real credentials or machine-specific paths.

## Dependencies

Task 14.

## Files Likely Touched

- `README.md`
- `docs/architecture.md`
- `docs/evaluation.md`
- `docs/provider-extensions.md`
- `examples/sample_outputs.md`

## Estimated Scope

Medium: 5 files.
