# Scope / story

Draft the tracker ticket from the structured intent produced in Scope / clarify.

## Purpose

Translate agreed intent into a well-formed ticket ready for tracker creation.
No repo access, no worklog — this step produces only the ticket draft.

## Inputs

- Agreed intent, success criteria, and constraints from Scope / clarify.
- Any answered questions from the question file.

## Draft the ticket

Write the following fields:

| Field | Guidance |
|---|---|
| **Title** | Imperative, ≤72 characters. State the outcome, not the solution. |
| **Description** | One paragraph: problem statement + why it matters now. |
| **Acceptance criteria** | Bulleted, observable, testable. One criterion per bullet. |
| **Labels** | Must include all three required labels from `config.yaml tracker.create.required_labels`: `type`, `priority`, `area`. |

### Label values (from `config.yaml`)

```yaml
required_labels: [type, priority, area]
```

Choose values appropriate to the work. Examples:

- `type`: `feat`, `fix`, `chore`, `docs`
- `priority`: `p0`, `p1`, `p2`, `p3`
- `area`: match an existing area label in the tracker (e.g. `backend`, `frontend`, `infra`)

## Output

A complete ticket draft in memory, ready to hand to **Scope / publish** for
deduplication and creation.

## Notes

- Keep the draft focused on *what* and *why* — not *how*.
- Do not include implementation details; those belong in Shape.
- If any acceptance criterion cannot be made observable, return to Scope / clarify.
