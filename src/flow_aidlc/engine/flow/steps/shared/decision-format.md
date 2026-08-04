# decision-format

A decision record captures a non-trivial choice that has trade-offs, so future
developers know what was decided and why, without reopening the question.

## When to graduate a decision

Promote a choice from `worklog/` to `knowledge/decisions/` when it meets any of
these criteria:

- It affects more than one stage or one slice.
- It rules out a reasonable alternative that may be re-proposed later.
- It changes a named convention or pattern used across the codebase.
- A reviewer or checkpoint discussion explicitly calls it a decision.

Minor in-stage choices (e.g., picking a variable name) stay in the journal only.

## File location and naming

```
knowledge/decisions/NNNN-<kebab-slug>.md
```

`NNNN` is a zero-padded four-digit integer. Increment from the highest existing
number in `knowledge/decisions/`. If the directory is empty, start at `0001`.

## File structure

```markdown
# NNNN — <Title>

**Status:** proposed | accepted | superseded by MMMM

**Date:** <ISO-8601 date>

**Task:** <PI-NNN>

## Context

<One paragraph: the situation that forced the choice.>

## Decision

<One or two sentences: exactly what was decided.>

## Consequences

<Bullet list: what becomes easier, what becomes harder, what is now ruled out.>

## Alternatives considered

<Optional. Bullet list of rejected options and the reason each was rejected.>
```

## Workflow

1. During Shape/design or Build/verify, identify a choice that meets the criteria.
2. Write the record using the structure above.
3. Append a journal entry: `[agent] Graduated decision to knowledge/decisions/NNNN-<slug>.md`.
4. Reference the decision number in the relevant worklog artifact (e.g., design.md).
