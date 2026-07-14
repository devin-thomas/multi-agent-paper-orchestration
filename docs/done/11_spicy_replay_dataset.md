# Task 11: Spicy Replay Dataset

## Goal

Add a reproducible randomized request fixture that gives repeat evaluators a materially different workload without changing the preserved original data.

## Scope

- Generate a separate CSV with the same request columns as the original fixture.
- Use a fixed seed so the randomized fixture can be regenerated exactly.
- Mix realistic order sizes, industries, events, dates, and catalog products.
- Document the new fixture and its regeneration command in the README and main plan.
- Add lightweight validation that the original fixture remains unchanged and the new fixture has the expected shape.

## Done When

- `data/quote_requests.csv` remains untouched.
- The new fixture is tracked separately and can be regenerated deterministically.
- README users can discover and replay the alternate workload.
