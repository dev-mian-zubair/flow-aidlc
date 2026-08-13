# Shape / map-existing

Produce a scoped map of the existing codebase before any new design decisions are
made. This step is **CONDITIONAL**: run it only for brownfield work (changes to
existing code). Skip it for pure greenfield additions with no touched files.

## Purpose

Survey the **relevant existing code** the ticket concerns — the terrain, not the
change — so requirements and design build on accurate ground rather than
assumptions. This step maps what *already exists*; it does **not** decide what to
change (that is `shape-design`'s job). You are surveying the neighbourhood the
ticket points at, not the exact files the eventual fix will edit.

## Seed from the ticket, then resolve structure from the graph

Do not explore blind, and do not grep for structure the code graph already knows.
Start from what Scope established, read the invariants, then let the graph give you
callers/dependents/contracts **deterministically**:

1. **Seed from the ticket.** Take the `Area` label and the **Affected
   file(s)/module(s)** from the ticket body as your starting coordinates.
2. **Seed from the Knowledge Map (invariants).** For each area the ticket touches,
   read the matching `docs/flow/knowledge/map/<subsystem>.md` (index:
   `docs/flow/knowledge/map/README.md`). These docs hold the **invariants and rationale** a graph can't know (e.g. "X is
   the single source of truth", "this toggle fails closed"); the *structure* lives in
   the graph (step 3).
3. **Resolve structure from the code graph (primary).** For each seed symbol/file,
   use the **universal ops** in [`steps/shared/graph.md`](../shared/graph.md) — query
   the graph MCP (`config.graph.mcp`, default `graphify`) or the CLI it maps to:
   - **`WHO_CALLS(symbol)`** → callers/dependents with `file:line`. This *is* the
     **don't-change list**, and it is deterministic — it catches indirect and
     method-resolved calls that grep silently misses.
   - **`NEIGHBORS(symbol)`** → the symbol's contract + immediate structure.
   - **`HUBS()`** (optional) → the subsystem's architectural surface, to spot
     load-bearing nodes the ticket didn't name.

   Cite results by their graph `file:line`. Do **not** hand-grep for callers when the
   graph can answer.
4. **Fallback to your own grep/glob survey — only where the graph can't answer.** For
   code **not yet in the committed graph** (new or uncommitted work), an **HTTP boundary
   between services** (an HTTP call is not an AST edge, so the regions don't connect — see
   the adapter), non-code config, or a **graph outage / staleness** (rebuild with the
   configured `graph.build`), survey that surface yourself with your `Grep` / `Glob` /
   `Read` tools — scoped to only the surface the graph could not resolve, seeded from the
   ticket's Area + Affected file(s)/module(s). Read only — make no edits or writes. State
   in the map when a fact came from this fallback rather than the graph.

## What to map

For each file or module in scope, record:

| Item | What to capture | Source |
|---|---|---|
| **File path** | Absolute path from repo root | seed / graph |
| **Public contracts** | Exported functions, API routes, event schemas, DB models | `NEIGHBORS` (graph) |
| **Callers / dependents** | Other symbols that import or call this one, with `file:line` | `WHO_CALLS` (graph) |
| **Don't-change list** | Interfaces that must stay stable (callers depend on them) | `WHO_CALLS` + Knowledge-Map invariants |

Limit the map to the **relevant existing surface** the ticket concerns (seeded
above). Do not map the full codebase — bound traversal to what the ticket touches
and its immediate callers, not the whole `WHO_CALLS` transitive closure.

## Output

Write the map to:

```
docs/flow/worklog/<TICKET-ID>/shape/map-existing.md
```

Format:

```markdown
## Relevant existing files

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
- **The map is a living input, not a final change-list.** It is a best-effort
  survey scoped from the ticket. If `shape-design` later reaches code this map did
  not cover, return here, widen the map for the newly-relevant surface, and
  re-present design against the updated map.
