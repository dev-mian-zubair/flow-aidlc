# Requirements — add-readonly-endpoint

## Intent

Operations and finance stakeholders need to see, at a glance, which departments
are close to exhausting their budget so they can intervene before overspend
occurs. This endpoint feeds that view in the observability dashboard.

## Functional Requirements

1. `GET /api/departments/over-budget` returns a JSON array of department
   objects (id, name, budget_used_pct) for every department whose
   `budget_used_pct >= 0.90`.
2. Budget figures are read from the `budgets` table only — no secondary cache,
   no denormalised column on `departments`.
3. The endpoint requires the caller to hold the `read_budget` RBAC permission,
   enforced via the `require_permissions(["read_budget"])` dependency.
4. SpiceDB resource-level access is checked with `check_resource_access`
   (action=`"read"`, resource_type=`"budget"`) for each department returned,
   so a user only sees departments they are authorised to view.
5. The response is sorted by `budget_used_pct` descending.

## Non-Functional Requirements

| Concern | Requirement | Rationale |
|---------|-------------|-----------|
| Performance | P95 latency < 200 ms under 50 concurrent callers | Dashboard refresh loop |
| Security | No write path; no mutation of any DB row | Read-only contract |
| Observability | Structured log on each call (caller user_id, result count) | Audit trail |
| Maintainability | No new derived copy of budget data | Budget has one source of truth |

## Acceptance Criteria

- [ ] `GET /api/departments/over-budget` with a valid `read_budget` token
      returns HTTP 200 and a list containing only departments at >= 90%.
- [ ] A caller without `read_budget` receives HTTP 403.
- [ ] The query touches only the `budgets` table (verified by query log in tests).
- [ ] `check_resource_access` filters out departments the caller cannot see.
- [ ] No Alembic migration is generated (schema is unchanged).

## Scope

### In scope

- New FastAPI route in `backend/app/api/`.
- Service helper in `backend/app/services/` to query `budgets` and compute
  `budget_used_pct`.
- Unit tests using the existing pytest fixtures.

### Out of scope

- Frontend UI changes (tracked separately).
- Writing or mutating any budget record.
- New database columns or tables (no migration).
- Caching layer on top of the `budgets` table.

### Open questions

- None — all authz paths are well-defined by existing guardrails.
