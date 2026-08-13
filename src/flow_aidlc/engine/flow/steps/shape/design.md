# Shape / design

Produce the component-level design and graduate cross-cutting decisions to the
shared knowledge base. This step is a **checkpoint**.

## Purpose

Decide *how* to implement the requirements — component boundaries, data flows,
interfaces, and any choices with meaningful trade-offs.

## Inputs

- Approved requirements from `docs/flow/worklog/<TICKET-ID>/shape/requirements.md`.
- Existing-code map from `docs/flow/worklog/<TICKET-ID>/shape/map-existing.md` (if present).

## Write the design document

Copy the template as the skeleton, then fill it in place:

```bash
cp .flow/templates/design.tmpl.md docs/flow/worklog/<TICKET-ID>/shape/design.md
```

Fill the SNAPSHOT header (Owner = you, Last updated = today), every `[Answer]:`,
the Components table, Data flow, API/Interface Contracts, Rollout/dark-ship,
Knowledge-map cross-check, Trade-offs, and Cross-Cutting Decisions sections.
Per `steps/shared/content-validation.md`, keep every template section — mark one
`<!-- N/A -->` rather than deleting a section that does not apply.

## Cross-check the design against the knowledge map

For each subsystem the design touches, compare the design against its
`docs/flow/knowledge/map/*.md` doc — which now holds the subsystem's **invariants** (structure
is in the code graph):

1. If the design honors the map's invariants, note "consistent" and move on.
2. **If the design would violate a stated invariant** (e.g. "X is the single source
   of truth", "this toggle fails closed"), stop — that is a load-bearing rule,
   enforced by a guardrail at Build/verify. Record it in the design's
   `## Knowledge-map cross-check` section and either redesign to honor it or, if the
   invariant itself is genuinely being changed, graduate that as a decision (below)
   and flag the doc + its `enforced-by:` guardrail for the `curator` (`/flow-refresh`).
3. For pure *structure* questions ("does this symbol still exist / who calls it"),
   ask the code graph, not the map.

## Graduate cross-cutting decisions

A decision is **cross-cutting** if it affects more than one task, establishes a
new pattern for the codebase, or has lasting architectural impact. **Adopting an
external dependency** (from Shape / research) is always cross-cutting — its ADR
cites `docs/flow/worklog/<TICKET-ID>/shape/research.md`.

For each cross-cutting decision in the design:

1. Create a record at `docs/flow/knowledge/decisions/NNNN-<slug>.md` following
   `steps/shared/decision-format.md`.
2. Add a link to that record in `docs/flow/worklog/<TICKET-ID>/shape/design.md` under a
   `## Graduated decisions` section.
3. Do **not** duplicate the rationale — the worklog design may summarise; the
   `docs/flow/knowledge/decisions/` record is the authoritative source.

Decisions that affect only this task stay in the worklog and are not graduated.

## CHECKPOINT

This is a checkpoint stage: the conductor dispatches the read-only `checkpoint-reviewer` to verify stage completeness (and traceability at the Shape→Build boundary) before `/flow-approve`. This agent does not dispatch it — it presents its artifact and returns.

**Stop here.** Present the design document and any graduated decision records to
the user. Wait for `/flow-approve` before advancing to Shape / slicing.

## Notes

- If a required interface change conflicts with the don't-change list from
  Shape / map-existing, raise it here rather than silently breaking the contract.
- Keep diagrams within `steps/shared/content-validation.md` rules.
