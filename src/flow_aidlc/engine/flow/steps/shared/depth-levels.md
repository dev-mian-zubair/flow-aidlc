# depth-levels

Every stage produces its required artifacts regardless of depth level.
Depth controls how much detail goes into those artifacts, not whether they exist.

## Levels

| Level    | When to use                                | Detail target                                  |
|----------|--------------------------------------------|------------------------------------------------|
| minimal  | Spike, prototype, or time-boxed exploration | Headings + one-line bullets; stubs for sections |
| standard | Normal feature work (default)              | Full prose per section; all fields populated   |
| deep     | High-risk, cross-cutting, or large feature  | Extended rationale; alternatives considered; diagrams required |

## How to apply

The depth level is set in `worklog/<PI-NNN>/progress.md` under
`Extension Configuration`. If no level is recorded, use **standard**.

Depth affects:

- **requirements.md** — minimal: acceptance criteria only; standard: + constraints + open questions; deep: + non-functional requirements + failure modes.
- **design.md** — minimal: approach paragraph; standard: + component map; deep: + sequence diagrams + decision records.
- **code-plan.md** — minimal: file list with one-line notes; standard: + per-file checkboxes; deep: + interface signatures + edge-case callouts.
- **verify.md** — minimal: smoke test; standard: + unit + lint; deep: + integration + performance baseline.

## Invariants

- A stage is never skipped because depth is minimal.
- Artifacts written at minimal depth may be promoted to standard in a later pass
  without a new stage; append, do not overwrite.
