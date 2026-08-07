# Consulting the Knowledge Map

`knowledge/map/` is the project's curated **Knowledge Map** — short, ≤1-screen
subsystem docs. Each doc holds a subsystem's **invariants and rationale** (the "why" and the
load-bearing rules); the *structure* it once described — files, symbols, callers —
now lives in the **code graph** (query it via `steps/shared/graph.md`). Reading the
map is **not** reading source: a Scope agent stays source-less and write-less while
using it for grounding.

## When

Consult on **every** Scope run — begin `clarify` by reading the index.

## How — the three-move recipe

1. **Index** — read `knowledge/map/README.md`; its table names each subsystem,
   what it covers, and its `derives-from` code globs. Pick the subsystem(s) the
   idea touches.
2. **Subsystem** — open the relevant `knowledge/map/<subsystem>.md` for its
   **invariants** and real vocabulary. For *structure* (which symbols, who calls
   what), query the code graph (`steps/shared/graph.md`).
3. **Affected modules** — use `.flow/knowledge-map.yaml`'s subsystem→path index to
   name **Affected file(s)/module(s)** at module / service granularity (or
   `QUERY`/`HUBS` on the graph). Exact `file:line` is **not** required at Scope —
   leave it optional; Shape/map-existing confirms precise files.

## What it grounds

- **Classification:** an idea spanning **multiple** map subsystems signals `epic`;
  a single subsystem signals `feat`/`bug`.
- **Epic decomposition:** split children along **real subsystem boundaries**.
- **Area labels + Affected files:** taken from the map, not guessed.
- **Dedup:** search the tracker with the subsystem's real vocabulary.

## Freshness

**Structural freshness was retired** — structure lives in the code graph, not in prose.
There is no more `verified-at-sha` / `freshness.py` / `STALE`-flag loop — a map's
structure can't go stale because structure now lives in the graph
(fresh-by-construction; rebuild it with the configured `graph.build` if the *graph*
itself is stale). A map's **invariants** stay honest a stronger way: each carries an
`enforced-by: <guardrail>` and the always-on guardrail **blocks** a change that
violates it at Build/verify — a hard gate, not a stale flag.

- **invariant vs code** → trust the map; if you suspect an invariant no longer
  holds, that's a guardrail concern (raise it), not a doc-drift flag.
- **not mapped** → if a needed area has no map, record it as an open question;
  never invent subsystem facts. For structural questions, ask the graph.

Use the map for **invariants and vocabulary**; use the graph for **structure**.

## Boundary

Read `knowledge/map/**` and `.flow/knowledge-map.yaml` only. Do **not** read
source files and do **not** write anything to the repository — Scope remains
write-less and source-less in the read sense.
