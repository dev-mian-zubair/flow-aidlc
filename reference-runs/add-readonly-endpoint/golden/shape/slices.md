# Slices — add-readonly-endpoint

Each slice is an independently verifiable unit of work. Slices are ordered so
that each one builds on — but does not break — the ones before it.

## Slice List

| ID | Scope | Files touched | Build order | Requirement refs |
|----|-------|---------------|-------------|-----------------|
| S1 | Service helper — query + filter | `services/department_service.py` | 1 of 3 | FR1, FR2 |
| S2 | Route + authz wiring | `api/department.py` | 2 of 3 | FR3, FR4, FR5 |
| S3 | Tests | `tests/api/test_department_over_budget.py` | 3 of 3 | All FRs, all ACs |

## Slice Detail

### Slice S1: Service helper — query and filter

**Scope:** Add `list_over_budget_departments(db, user, threshold=0.90)` to
`services/department_service.py`. Queries the `budgets` table, computes
`budget_used_pct = budget.spend / budget.limit`, filters to >= threshold,
sorts descending. Returns a list of plain dicts (no HTTP concerns here).

**Files:**

- `backend/app/services/department_service.py`

**Build order:** 1 of 3

**Requirement refs:** FR1, FR2 (reads `budgets` only, no migration)

**Done when:**

- [ ] `list_over_budget_departments` exists and returns only rows above threshold.
- [ ] Query plan touches `budgets` table, not any denormalised column.
- [ ] Unit test for the helper passes with a seeded in-memory SQLite fixture.

---

### Slice S2: Route and authz wiring

**Scope:** Add `GET /api/departments/over-budget` to `api/department.py`.
Apply `require_permissions(["read_budget"])` as a FastAPI dependency.
Call `check_resource_access(db, current_user, "budget", dept_id, action="read")`
per result row to enforce ReBAC, filtering out rows the caller cannot see.

**Files:**

- `backend/app/api/department.py`

**Build order:** 2 of 3

**Requirement refs:** FR3 (RBAC), FR4 (ReBAC/SpiceDB), FR5 (sort order)

**Done when:**

- [ ] Route registered and reachable at `GET /api/departments/over-budget`.
- [ ] Request without `read_budget` token returns HTTP 403.
- [ ] `check_resource_access` called once per result row.

---

### Slice S3: Tests

**Scope:** pytest tests covering the happy path, the 403 path, the threshold
filter, and the `check_resource_access` filtering. No migration required — test
DB is seeded via existing fixtures.

**Files:**

- `backend/tests/api/test_department_over_budget.py`

**Build order:** 3 of 3

**Requirement refs:** All functional requirements and acceptance criteria

**Done when:**

- [ ] Happy-path test: authorised user, two departments over threshold → 200.
- [ ] Forbidden test: user without `read_budget` → 403.
- [ ] ReBAC filter test: `check_resource_access` returning False hides the row.
- [ ] No migration in `backend/app/db/migrations/versions/` after running tests.
