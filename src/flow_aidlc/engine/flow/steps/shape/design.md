# Shape / design

Produce the component-level design and graduate cross-cutting decisions to the
shared knowledge base. This step is a **checkpoint**.

## Purpose

Decide *how* to implement the requirements — component boundaries, data flows,
interfaces, and any choices with meaningful trade-offs.

## Inputs

- Approved requirements from `worklog/<PI-NNN>/shape/requirements.md`.
- Existing-code map from `worklog/<PI-NNN>/shape/map-existing.md` (if present).

## Write the design document

Copy the template as the skeleton, then fill it in place:

```bash
cp .flow/templates/design.tmpl.md worklog/<PI-NNN>/shape/design.md
```

Fill the SNAPSHOT header (Owner = you, Last updated = today), every `[Answer]:`,
the Components table, Data flow, API/Interface Contracts, Rollout/dark-ship,
Knowledge-map cross-check, Trade-offs, and Cross-Cutting Decisions sections.
Per `steps/shared/content-validation.md`, keep every template section — mark one
`<!-- N/A -->` rather than deleting a section that does not apply.

## Cross-check the design against the knowledge map

For each subsystem the design touches, compare the design against its
`knowledge/map/*.md` doc:

1. If the design is consistent with the map, note "consistent" and move on.
2. **If the code contradicts the map, the code wins.** Record the discrepancy
   in the design's `## Knowledge-map cross-check` section and flag the relevant
   `knowledge/map/*.md` doc stale.
3. Stale map docs are re-derived automatically by `/flow-refresh` (the `curator`
   agent, `flow_aidlc.checks.freshness`) — this cross-check feeds that loop. You do
   not need to fix the map doc manually; just flag it.

## Graduate cross-cutting decisions

A decision is **cross-cutting** if it affects more than one task, establishes a
new pattern for the codebase, or has lasting architectural impact. **Adopting an
external dependency** (from Shape / research) is always cross-cutting — its ADR
cites `worklog/<PI-NNN>/shape/research.md`.

For each cross-cutting decision in the design:

1. Create a record at `knowledge/decisions/NNNN-<slug>.md` following
   `steps/shared/decision-format.md`.
2. Add a link to that record in `worklog/<PI-NNN>/shape/design.md` under a
   `## Graduated decisions` section.
3. Do **not** duplicate the rationale — the worklog design may summarise; the
   `knowledge/decisions/` record is the authoritative source.

Decisions that affect only this task stay in the worklog and are not graduated.

## CHECKPOINT

Before presenting for `/flow-approve`, dispatch the read-only `checkpoint-reviewer` subagent to verify stage completeness (and traceability at the Shape→Build boundary).

**Stop here.** Present the design document and any graduated decision records to
the user. Wait for `/flow-approve` before advancing to Shape / slicing.

## Notes

- If a required interface change conflicts with the don't-change list from
  Shape / map-existing, raise it here rather than silently breaking the contract.
- Keep diagrams within `steps/shared/content-validation.md` rules.
