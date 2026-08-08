# decision-log

A compact, append-only trail of checkpoint outcomes, stage skips, map
discrepancies, and handoffs — one line per event, kept in `progress.md`.

## File location

```
worklog/<TICKET-ID>/progress.md   (## Decision log section)
```

Not a standalone file. Lives at the bottom of the task's `progress.md`.

## Line format

```
YYYY-MM-DDTHH:MM:SSZ · <stage> · <decision ≤10 words> · <rationale ≤20 words>
```

`<stage>` is a Flow stage name from the per-stage table in `playbook.md`
(e.g. `Scope/clarify`, `Shape/design`, `Build/verify`, `Ship/learnings`).

## When to append

Append one line at each of the following events:

- **Checkpoint approved** — stage outcome confirmed; next stage authorised.
- **Stage skipped** — e.g. `Shape/map-existing` skipped for greenfield work.
- **Map discrepancy** — reality differs from knowledge/map/ after a codebase scan.
- **Handoff** — task handed to another agent or paused across sessions.

## How it differs from the other logs

| | decision-log | journal.md | knowledge/decisions/ |
|---|---|---|---|
| **Voice** | terse (one line) | verbose (raw, verbatim) | structured (multi-section) |
| **Scope** | per-gate events only | everything that happened | cross-cutting, codebase-wide |
| **Mutability** | append-only | append-only | immutable once accepted |
| **Audience** | quick status scan | full audit trail | future maintainers |

The journal captures every detail; the decision-log is the navigable spine.
Cross-cutting choices with trade-offs graduate to `knowledge/decisions/` via
`steps/shared/decision-format.md`.

## Rules

- **Append only.** Never rewrite or delete a past line.
- **One line per event.** Do not combine two events into one entry.
- **UTC timestamps** with `Z` suffix.
- Stage name must match the `Phase/Stage` naming in `playbook.md`.

## Examples

```
2026-08-03T09:14:00Z · Scope/publish · ticket ABC-042 approved, scope locked · requirements stable, no outstanding questions
2026-08-03T11:30:22Z · Shape/map-existing · skipped — greenfield module, no prior surface · no existing files under src/billing/
2026-08-04T08:05:44Z · Build/verify · guardrail test-coverage passed · new logic covered, no untested branches remain
```
