# Architecture Notes

The passing capstone uses a five-agent pydantic-ai workflow:

1. `OrchestratorAgent` plans the route, delegates work, validates outputs, and creates the final customer response.
2. `IntakeAgent` parses customer text into structured request facts.
3. `InventoryAgent` checks stock, shortages, reorder needs, and supplier delivery dates.
4. `QuotingAgent` prepares explainable quote lines from catalog pricing, volume discounts, and quote history.
5. `SalesAgent` records only validated, fully fulfillable firm orders.

The refactor should keep this architecture intact while moving each responsibility into a focused module.

The important production pattern is not "let the model do everything." The current solution uses LLM agents for language interpretation, structured reasoning, and customer response drafting, then deterministic validation for catalog names, inventory math, pricing, transaction plans, and response safety.

## Provider Boundary

`paper_orchestration.providers.first_class` adapts the four supported profiles to Pydantic AI:

- OpenAI uses `OpenAIChatModel` and `OpenAIProvider`.
- Anthropic uses `AnthropicModel` and `AnthropicProvider`.
- Gemini uses `GoogleModel` and `GoogleProvider`.
- Ollama uses `OpenAIChatModel` with its OpenAI-compatible local endpoint.

The model factory performs provider-specific credential and endpoint validation before agent
construction. The adapters report the profile's structured-output and tool-calling capabilities,
so an incomplete profile still fails the shared preflight contract. No adapter performs a network
request while being constructed.

The default installation already included OpenAI and Pydantic AI; Task 10 adds the direct
`anthropic` and `google-genai` dependencies so all four adapters are available from one install.
The installed versions are verified with `pip check`; Ollama needs no separate SDK because its
adapter uses the OpenAI-compatible HTTP interface.

