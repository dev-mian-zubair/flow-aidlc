# Shape / slicing

Decompose the approved design into ordered build slices.

## Purpose

Break the work into independently executable slices so that each Build iteration
has a clear, bounded scope. A slice is the smallest unit of work that produces a
testable increment.

## Inputs

- Approved design from `docs/flow/worklog/<TICKET-ID>/shape/design.md`.
- Approved requirements from `docs/flow/worklog/<TICKET-ID>/shape/requirements.md` (for requirement
  reference ids).

## Slicing rules

- Each slice must be independently deployable or at minimum independently testable.
- A slice must not span more components than can be reviewed in a single code-review
  pass (rough guide: ≤5 files changed).
- Order slices to minimise blocked dependencies: foundational work (models, schemas,
  migrations) before features that depend on them.
- Every slice must reference at least one requirement id.

## Write slices.md

Copy the template as the skeleton, then fill it in place:

```bash
cp .flow/templates/slices.tmpl.md docs/flow/worklog/<TICKET-ID>/shape/slices.md
```

Fill the SNAPSHOT header (Owner = you, Last updated = today), the `## Slice List`
table (one row per slice), and a `### Slice <ID>:` detail block for every slice,
including the `**Requirement refs:**` line on each block.

> **Important:** The Slice Detail `### Slice <ID>:` headers and each slice's
> `**Requirement refs:**` line are what the traceability check parses — keep that
> format exactly. A bare `## Slices` table is NOT parsed and will cause every
> requirement to appear orphaned.

## Traceability check

After writing `slices.md`, run the traceability check to confirm every requirement
is covered by at least one slice:

```bash
python -m flow_aidlc.checks.traceability docs/flow/worklog/<TICKET-ID> --write
```

This emits `docs/flow/worklog/<TICKET-ID>/shape/traceability.md` (the requirement→slice
coverage matrix) and exits non-zero if any FR or NFR is uncovered.

**The slicing stage is not complete while any requirement is orphaned.** Resolve
each orphan by adding it to an existing slice's requirement refs or by adding a
new slice, then re-run the check until it exits 0.

Orphan slices (a slice that cites a requirement ID not found in `requirements.md`)
are warnings to review — they are not blockers, but they often indicate a typo or
a stale ID that should be corrected.

See `steps/shared/traceability.md` for the full traceability guide.

## Output

Hand `slices.md` and `shape/traceability.md` to **Build / slice-design** (the
first slice). The Build phase processes one slice at a time in the order listed.

## Notes

- If slicing reveals a scope that is significantly larger than expected, surface
  that now and consider returning to Scope / story to adjust the ticket's acceptance
  criteria before entering Build.
- Slice ids are stable — do not renumber after Build has started.
