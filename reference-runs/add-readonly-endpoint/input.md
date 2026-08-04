Add a read-only GET endpoint that lists all departments currently over 90% of
their budget. The endpoint is internal-facing (used by the observability
dashboard) and must be accessible only to users who hold the `read_budget`
permission. It reads directly from the `budgets` table — the single source of
truth — and must not introduce a new derived copy of budget data. No database
schema changes are required.
