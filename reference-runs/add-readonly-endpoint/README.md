# Golden Reference Case: add-readonly-endpoint

This directory holds the hand-authored golden reference for the task described
in `input.md` — adding a read-only GET endpoint that lists departments over
90% of their budget.

## Directory layout

```
add-readonly-endpoint/
├── input.md             Task description (the intent)
├── baseline.yaml        Regression threshold (min_overall: 0.75)
├── README.md            This file
└── golden/
    └── shape/
        ├── requirements.md   Functional + non-functional requirements
        ├── design.md         Component design and API contract
        └── slices.md         Ordered build slices
```

## Scoring a live candidate against this golden

A live Flow-run for this task produces shape artifacts under a worklog
directory, typically `worklog/<task-slug>/shape/`. Once that run is complete,
score it from the `scripts/flow-checks/` directory:

```bash
cd scripts/flow-checks
python -m flow_checks.reference_check \
    reference-runs/add-readonly-endpoint \
    /path/to/worklog/<task-slug>
```

The candidate path is the worklog root (which contains `shape/`), NOT
`.../shape` — files are paired by path relative to each root, and the golden
root already holds `shape/design.md` etc., so the candidate root must mirror
that layout for the relative paths to match.

The command prints per-file scores and an overall mean, then exits with:

- **0** — mean_overall >= 0.75 (PASS)
- **1** — mean_overall < 0.75 (FAIL — regression below baseline)

**Note:** generating the candidate requires a live Flow-run; CI does not do
this. CI instead runs the golden-vs-golden self-consistency smoke (below).

## CI smoke (golden vs itself)

The gate (`python -m flow_checks.gate`) includes a CHECK 4/4 that scores
the golden directory against itself. Because identical texts yield
`overall == 1.0`, this proves the scorer and the reference fixture are both
well-formed, with no LLM or network required.

To run just the self-consistency check manually:

```bash
cd scripts/flow-checks
python -m flow_checks.reference_check \
    reference-runs/add-readonly-endpoint \
    reference-runs/add-readonly-endpoint/golden
```

The candidate path is `.../golden` (NOT `.../golden/shape`): `score_dirs`
pairs files by path relative to each root, so the candidate root must be
`golden/` for `shape/design.md` et al. to match.

Expected output:

```
  shape/design.md                                               overall=1.0000
  shape/requirements.md                                         overall=1.0000
  shape/slices.md                                               overall=1.0000
mean_overall: 1.0000  (threshold: 0.75)  PASS
```

## What makes this golden "good"

The three artifact files (`requirements.md`, `design.md`, `slices.md`) were
hand-authored to reflect two hard guardrails from the PIP codebase:

1. **authz-completeness** — the endpoint gates on both an RBAC permission
   (`require_permissions(["read_budget"])`) and a ReBAC SpiceDB resource check
   (`check_resource_access`). Both must appear in requirements and design.

2. **budget-integrity** — budget figures come from the `budgets` table only.
   No new derived copy, no cache, no denormalised column, no migration.
