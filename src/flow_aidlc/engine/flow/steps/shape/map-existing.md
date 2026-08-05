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

## Seed from the ticket, then explore

Do not explore blind. Start from what Scope already established, then drill in:

1. **Seed from the ticket.** Take the `Area` label and the **Affected
   file(s)/module(s)** from the ticket body as your starting coordinates.
2. **Seed from the Knowledge Map.** For each area the ticket touches, read the
   matching `knowledge/map/<subsystem>.md` (index: `knowledge/map/README.md`) for
   the curated subsystem picture — contracts and boundaries are already summarised
   there. Note its freshness (`status:` / `verified-at-sha`); if stale, treat it
   as a hint and verify against code.
3. **Explore outward.** Delegate to the `Explore` agent (read-only, scoped) to
   confirm and extend the seed with concrete, current detail:

   ```
   Agent: Explore
   Scope: the relevant existing surface the ticket concerns — seeded from the
          ticket's Area + Affected file(s)/module(s) and the Knowledge Map
          subsystem doc(s); expand only as contracts/callers require.
   Depth: medium (adjust to deep if the relevant surface is large)
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

Limit the map to the **relevant existing surface** the ticket concerns (seeded
above). Do not map the full codebase.

## Output

Write the map to:

```
worklog/<PI-NNN>/shape/map-existing.md
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
