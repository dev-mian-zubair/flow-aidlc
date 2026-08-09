# Design — [Task ID]

> **Status:** SNAPSHOT · **Owner:** [Answer]: · **Last updated:** [Answer]:

## Approach

High-level strategy: what will change, what will stay the same, and why this approach over alternatives.

[Answer]:

## Components

List each component (service, module, route, model, hook, etc.) involved.

| Component | Layer | Role | New / Modified / Unchanged |
|-----------|-------|------|---------------------------|
| [Answer]: | [Answer]: | [Answer]: | [Answer]: |

## Data flow

[Answer]: <!-- prose or ASCII diagram of the key data path -->

## API / Interface Contracts

Document new or changed API surfaces (REST endpoints, function signatures, event shapes, etc.).

### [Endpoint / Function name]

- Method / signature: [Answer]:
- Request / input: [Answer]:
- Response / output: [Answer]:
- Auth / permissions: [Answer]:
- Error cases: [Answer]:

## Rollout / dark-ship

Risky changes ship dark behind a default-OFF flag. Name the flag + default,
or state why none is needed.

[Answer]:

## Knowledge-map cross-check

For each touched subsystem, note whether the design honors its
`docs/flow/knowledge/map/*.md` **invariants** (structure lives in the code graph).
A design that would violate a stated invariant is a load-bearing rule enforced by a
guardrail at Build/verify — redesign to honor it, or graduate the change as a
decision and flag the doc's `enforced-by:` guardrail for the curator. "consistent"
if none.

| Subsystem (map doc) | Honors invariants? | Violation (redesign or graduate) |
|---------------------|-------------|-------------------------|
| [Answer]: | [Answer]: | [Answer]: |

## Trade-offs

| Option | Chose? | Reason |
|--------|--------|--------|
| [Answer]: | [Answer]: | [Answer]: |

## Cross-Cutting Decisions

List any decision that affects more than one component. Graduate each to
`docs/flow/knowledge/decisions/NNNN-<slug>.md` using `decision.tmpl.md`.

| Decision | Decision file |
|----------|---------------|
| [Answer]: | `docs/flow/knowledge/decisions/NNNN-[Answer]:` |

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| [Answer]: | [Answer]: | [Answer]: | [Answer]: |
