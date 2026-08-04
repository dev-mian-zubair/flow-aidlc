# Scope / story

Draft the tracker ticket from the structured intent produced in Scope / clarify.

## Purpose

Translate agreed intent into a well-formed ticket ready for tracker creation.
No repo access, no worklog — this step produces only the ticket draft.

## Inputs

- Agreed intent, **ticket type** (`bug | task | feat | epic`), success criteria,
  and constraints from Scope / clarify.
- For an epic: the agreed **child breakdown** (list of child stubs).
- Any answered questions from the conversation.

## Draft from the type's template

Select the body template for the confirmed ticket type and fill every
`<placeholder>` from the clarify output:

| Type | Template |
|------|----------|
| `bug`  | `templates/scope/bug.tmpl.md` |
| `task` | `templates/scope/small-task.tmpl.md` |
| `feat` | `templates/scope/feature.tmpl.md` |
| `epic` | `templates/scope/epic.tmpl.md` (parent) **+ one child stub per child** |

Each template has an `ISSUE BODY` block (created as the issue body) and a
`NATIVE FIELDS` block (labels / type / board fields / milestone / parent —
set by Scope / publish, not typed into the body). Fill both.

**Acceptance criteria** are checkbox lines (`- [ ] AC1: <observable outcome>`) —
if a criterion can't be checked by running something, rewrite it.

**Severity ↔ Priority sync (bug):** the body Severity, the `priority:` label, and
the board Priority field must all carry the same value — don't let them drift.

**Ground in the Knowledge Map:** fill **Affected file(s)/module(s)** and choose
`area` labels from `knowledge/map/` — module-level names via the
`.flow/knowledge-map.yaml` `derives-from` globs (see `steps/shared/knowledge-map.md`).
Exact `file:line` stays optional at Scope; Shape/map-existing confirms it.

### Epic → parent + child stubs (hybrid)

For an epic, draft:

1. The **Epic parent** from `epic.tmpl.md` — goal, epic-level success criteria,
   in-scope / non-goals, and a **child checklist** (`- [ ] <child title>`; the
   real `#numbers` are filled in by publish once children exist).
2. **One stub per child** from its own `feat`/`task` template, filling only the
   lightweight fields the clarify breakdown produced (title, why / exact-change,
   type, size). Leave detailed acceptance criteria as `<to be authored in this
   child's Shape phase>` — stubs are intentionally thin.

### Label values (from `config.yaml tracker.create.required_labels`)

Required on every ticket: `type`, `priority`, `area`.

- `type`: `bug` · `feat` · `task` · `epic` (matches the ticket type; a child
  carries its own `feat`/`task`)
- `priority`: `P0` · `P1` · `P2` · `P3` (uppercase — keep in sync with the body
  Severity and the board Priority field)
- `area`: an existing area label in the tracker (e.g. `backend`, `frontend`,
  `infra`); more than one is allowed

## Output

A complete ticket draft in memory, ready to hand to **Scope / publish** for
deduplication and creation.

## Notes

- Keep the draft focused on *what* and *why* — not *how*.
- Do not include implementation details; those belong in Shape.
- If any acceptance criterion cannot be made observable, return to Scope / clarify.
