# Architecture Notes

The passing capstone uses a five-agent pydantic-ai workflow:

1. `OrchestratorAgent` plans the route, delegates work, validates outputs, and creates the final customer response.
2. `IntakeAgent` parses customer text into structured request facts.
3. `InventoryAgent` checks stock, shortages, reorder needs, and supplier delivery dates.
4. `QuotingAgent` prepares explainable quote lines from catalog pricing, volume discounts, and quote history.
5. `SalesAgent` records only validated, fully fulfillable firm orders.

The refactor should keep this architecture intact while moving each responsibility into a focused module.

The important production pattern is not "let the model do everything." The current solution uses LLM agents for language interpretation, structured reasoning, and customer response drafting, then deterministic validation for catalog names, inventory math, pricing, transaction plans, and response safety.

