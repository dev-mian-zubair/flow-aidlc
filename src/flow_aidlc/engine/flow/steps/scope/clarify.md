# Scope / clarify

Turn a raw idea into structured intent before writing a single line of code or a
ticket.

## Purpose

Extract the real goal, surface ambiguity, and agree on what success looks like.
No repo access, no worklog — this step produces only a question file.

## Powered by superpowers

Invoke `superpowers:brainstorming` now. Let it explore the idea freely before
committing to any framing.

```
/superpowers:brainstorming
```

Use the brainstorming output to identify:

- The core user or system need.
- What "done" looks like (observable outcome, not implementation).
- Constraints: time-box, tech limits, out-of-scope boundaries.
- Open questions that must be answered before story-writing can proceed.

## Clarify open questions

For every open question that cannot be resolved in the current conversation,
ask it inline in the chat. This step is **repo-less and worklog-less** — no
files are written to the repository. If a durable record is needed, capture
the answer in a ticket comment after the task id is assigned.

Questions stay in the conversation — never silently skip an unresolved blocker.

Apply `steps/shared/overconfidence-prevention.md` when deciding whether to ask
vs infer — never proceed past unresolved ambiguity.

## Ground in the Knowledge Map

Before classifying, consult the curated Knowledge Map — see
`steps/shared/knowledge-map.md`. Read `knowledge/map/README.md` (the index) on every
run and open the subsystem map(s) the idea touches. Reading the map is **not**
reading source; Scope stays source-less and write-less.

Use it to ground the classification, epic decomposition, and `area` below in real
subsystem boundaries and names. Honor the freshness rule: the authoritative signal
is git history vs each doc's `verified-at-sha`, **not** the `status:` line —
see `steps/shared/knowledge-map.md`. Treat a stale map as provisional, and an unmapped
area as an open question, never an invention.

## Classify the ticket type

After intent is clear, classify the work into exactly one type. **Propose the
type with a one-line rationale and confirm with the user** — never infer silently
(the type drives which template and which publish path is used).

| Type | Test | Outcome |
|------|------|---------|
| `bug`  | Corrects broken or unintended behavior in existing code | one ticket → `templates/scope/bug.tmpl.md` |
| `task` | Trivial, mechanical, narrow; a single observable criterion | one ticket → `templates/scope/small-task.tmpl.md` |
| `feat` | Net-new capability that fits **one** Shape→Build→Ship cycle | one ticket → `templates/scope/feature.tmpl.md` |
| `epic` | Initiative too large for one cycle — multiple independent deliverables, spans subsystems, or would produce many unrelated slices | **parent + child stubs** (see below) |

The `feat`↔`epic` line is the decomposition test: if the idea is several
independent pieces, it is an epic and must be split before any single ticket is
drafted.

## Epic decomposition (only when type = epic)

Epics use the **hybrid** model: create the umbrella now, and each child as a
*stub* — its full acceptance criteria and design are authored later when the
child is picked up in its own Shape phase.

1. Propose an ordered **child breakdown**: for each child give `{type (feat|task),
   one-line title, one-line why, rough size (S|M|L)}`. Keep it **one level deep** —
   a child is never itself an epic here; if one looks epic-sized, flag it, don't
   recurse.
2. Review interactively with the user — add / merge / split / drop children until
   the set is agreed. Apply `steps/shared/overconfidence-prevention.md`.
3. The agreed breakdown is handed to **Scope / story**, which drafts the Epic
   parent (`templates/scope/epic.tmpl.md`) plus one stub per child.

## Output

A shared understanding of:

- **Intent:** one sentence stating the goal.
- **Ticket type:** one of `bug | task | feat | epic`, confirmed with the user.
- **Success criteria:** two to five observable outcomes.
- **Constraints:** what is explicitly out of scope.
- **Child breakdown:** (epic only) the agreed list of child stubs.
- **Open questions:** captured in conversation (may be empty if none remain).

Hand off to **Scope / story** once intent + type are agreed and any blocking
questions are answered.

## Notes

- This step is **source-less and write-less** — you MAY read `knowledge/map/`
  (the curated Knowledge Map) for grounding, but do not read or modify any source
  file, and write nothing to the repository.
- Do not create a worklog entry; the worklog is created in `steps/shared/kickoff.md`
  only after a task id is assigned (Scope / publish).
