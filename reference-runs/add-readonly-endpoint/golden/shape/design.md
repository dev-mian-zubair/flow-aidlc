# Design — add-readonly-endpoint

## Approach

Add a single read-only FastAPI route that delegates to a thin service function.
The service queries the `budgets` table directly, computes the usage percentage
inline, filters to >= 90%, then applies `check_resource_access` per department
to honour the ReBAC layer. No new table, no cache, no migration.

This approach keeps the `budgets` table as the unique source of truth (per the
budget-integrity guardrail) and layers the two required authz checks as the
existing codebase requires: RBAC via `require_permissions(["read_budget"])`
and ReBAC via `check_resource_access`.

## Components

| Component | Layer | Role | New / Modified / Unchanged |
|-----------|-------|------|---------------------------|
| `api/department.py` | API | Route definition for `GET /api/departments/over-budget` | Modified |
| `services/department_service.py` | Service | `list_over_budget_departments(db, user, threshold)` | Modified |
| `core/permissions.py` | Auth | `require_permissions(["read_budget"])`, `check_resource_access` | Unchanged |
| `models/budget.py` | ORM | `Budget` model — source of truth for spend data | Unchanged |
| `tests/api/test_department_over_budget.py` | Test | Endpoint-level tests with mock auth fixtures | New |

## API / Interface Contracts

### GET /api/departments/over-budget

- Method / signature: `GET /api/departments/over-budget?threshold=0.90`
- Request / input: optional `threshold` query param (float, default 0.90);
  bearer token in `Authorization` header.
- Response / output:
  ```json
  [
    {"id": 42, "name": "Engineering", "budget_used_pct": 0.97},
    {"id": 7,  "name": "Marketing",  "budget_used_pct": 0.91}
  ]
  ```
- Auth / permissions: `require_permissions(["read_budget"])` (RBAC);
  `check_resource_access(db, user, "budget", dept_id, action="read")` per row
  (ReBAC via SpiceDB).
- Error cases: 403 if missing `read_budget`; 422 if threshold out of [0, 1].

## Cross-Cutting Decisions

No new cross-cutting decisions — existing authz patterns apply.

| Decision | Decision file |
|----------|---------------|
| Budget has one source of truth: `budgets` table | `knowledge/decisions/0003-budget-source-of-truth.md` |

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Full-table scan on `budgets` at high volume | Low | Medium | Existing index on `budget_id`; add composite index if P95 exceeds SLO |
| ReBAC check per row adds latency | Medium | Low | Batch SpiceDB check if row count grows; acceptable for now |
