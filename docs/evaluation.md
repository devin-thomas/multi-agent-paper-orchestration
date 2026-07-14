# Evaluation Notes

The passing submission evaluated the system against `quote_requests_sample.csv` and wrote `test_results.csv`.

Preserved baseline:

- 20 requests processed
- 5 fulfilled sales recorded
- 5 quote-ready outcomes
- 7 partial quotes needing review
- 3 unfulfilled requests
- 5 requests with cash-balance changes
- $1,413.50 gross sales
- $628.23 restock spend
- $785.27 net cash change

The portfolio refactor should preserve these columns where practical:

- request metadata
- requested delivery date
- order status
- cash and inventory before/after
- gross sales, restock spend, expected and actual cash delta
- fulfilled and unfulfilled items
- agent route
- tool calls
- response quality findings
- customer response

## Model Selection

The evaluation CLI accepts only the global `--profile` and `--model` model-selection overrides.
Credentials, endpoints, and per-agent overrides remain configuration-only. Before initializing
the SQLite database, the runner preflights the orchestrator, intake, inventory, quoting, and
sales roles. It writes the selected profile, global model, and resolved per-agent models to the
secret-free `evaluation_metadata.json` artifact beside the CSV output.

