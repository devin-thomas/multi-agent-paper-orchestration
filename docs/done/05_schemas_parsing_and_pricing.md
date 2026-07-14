# Task 05: Schemas, Parsing, And Pricing

## Goal

Move typed models, request parsing, catalog canonicalization, and pricing rules into deterministic modules.

## Scope

- Move Pydantic models to `schemas.py`.
- Move request text cleanup, item extraction, and date parsing to `parsing.py`.
- Move unit price, wholesale cost, and discount logic to `pricing.py`.
- Add focused tests for parsing and price math.

## Done When

- Edge cases such as unknown items, A4/copy paper, quantity consolidation, and requested dates are covered.
- Pricing totals remain deterministic and easy to audit.
