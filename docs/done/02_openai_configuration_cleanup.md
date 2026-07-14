# Task 02: OpenAI Configuration Cleanup

## Goal

Remove Vocareum-specific configuration and make the project use normal OpenAI settings.

## Scope

- Replace `UDACITY_OPENAI_API_KEY` with `OPENAI_API_KEY`.
- Remove the forced `OPENAI_BASE_URL=https://openai.vocareum.com/v1`.
- Support `OPENAI_MODEL` or retain `BEAVERS_CHOICE_AGENT_MODEL` as a backwards-compatible alias.
- Add clear missing-key errors.
- Keep `.env.example` accurate.

## Done When

- A local `.env` with `OPENAI_API_KEY` is enough for live agent execution.
- No code path assumes Vocareum.
- README quick start matches the runtime behavior.

