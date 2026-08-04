# Shape / map-existing

Produce a scoped map of the existing codebase before any new design decisions are
made. This step is **CONDITIONAL**: run it only for brownfield work (changes to
existing code). Skip it for pure greenfield additions with no touched files.

## Purpose

Understand what is already there — files, contracts, and boundaries — so the
requirements and design steps build on accurate ground rather than assumptions.

## Prefer the Explore agent

Delegate the mapping work to the `Explore` agent. It is optimised for read-only,
scoped repository search.

```
Agent: Explore
Scope: files touched by <PI-NNN> (from ticket acceptance criteria and title)
Depth: medium (adjust to deep if the touched surface is large)
```

The `Explore` agent must **read only** — no edits, no writes.

## What to map

For each file or module in scope, record:

| Item | What to capture |
|---|---|
| **File path** | Absolute path from repo root |
| **Public contracts** | Exported functions, API routes, event schemas, DB models |
| **Callers / dependents** | Other files that import or call this file |
| **Don't-change list** | Interfaces that must stay stable (other callers depend on them) |

Limit the map to the touched surface. Do not map the full codebase.

## Output

Write the map to:

```
worklog/<PI-NNN>/shape/map-existing.md
```

Format:

```markdown
## Touched files

- `path/to/file.py` — <one-line role>

## Contracts (must stay stable)

- `FunctionName(args) -> ReturnType` in `path/to/file.py`

## Don't-change list

- <item> — <reason>
```

Hand off to **Shape / requirements** once the map is written.

## Notes

- If the scope cannot be bounded (too many callers), flag this in the map and
  raise it in Shape / requirements as a constraint.
- Do not make design decisions here — only observe and record.
