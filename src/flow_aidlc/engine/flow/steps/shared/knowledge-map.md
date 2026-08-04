# Consulting the Knowledge Map

`knowledge/map/` is the project's curated **Knowledge Map** — descriptive,
≤1-screen subsystem docs, re-derived from code by the `curator` agent. Reading
the map is **not** reading source: a Scope agent stays source-less and write-less
while using the map for grounding.

## When

Consult on **every** Scope run — begin `clarify` by reading the index.

## How — the three-move recipe

1. **Index** — read `knowledge/map/README.md`; its table names each subsystem,
   what it covers, and its `derives-from` code globs. Pick the subsystem(s) the
   idea touches.
2. **Subsystem** — open the relevant `knowledge/map/<subsystem>.md` for structure
   and real naming.
3. **Affected modules** — use `.flow/knowledge-map.yaml` `derives-from` globs to
   name **Affected file(s)/module(s)** at module / service granularity. Exact
   `file:line` is **not** required at Scope — leave it optional; Shape/map-existing
   confirms precise files.

## What it grounds

- **Classification:** an idea spanning **multiple** map subsystems signals `epic`;
  a single subsystem signals `feat`/`bug`.
- **Epic decomposition:** split children along **real subsystem boundaries**.
- **Area labels + Affected files:** taken from the map, not guessed.
- **Dedup:** search the tracker with the subsystem's real vocabulary.

## Freshness — the authoritative signal

The map's `status:` frontmatter line is only a **hint**. It is updated by the
curator or the worklog-scoped freshness hook, so a change made outside a Flow
worklog (a teammate's commit, a merge) can leave `status: FRESH` on a doc that is
actually stale.

The **authoritative** freshness signal is git history vs the doc's
`verified-at-sha`: a map doc is stale when the code its `derives-from` globs match
has changed since its recorded `verified-at-sha`. The Scope **orchestrator** (the
main loop that runs `/flow-scope`, which has shell access) computes the stale list
at the start of a run and passes it into `clarify`; a least-privilege scope
subagent that cannot run it falls back to the `status:` line as a weaker hint.

- **stale** → use the doc with a caveat, tell the user, and suggest
  `/flow-refresh` before relying on details.
- **not mapped** → if a needed area has no map, record it as an open question;
  never invent subsystem facts.

Use the map for **structure and naming**, not exact line numbers (those drift).

## Boundary

Read `knowledge/map/**` and `.flow/knowledge-map.yaml` only. Do **not** read
source files and do **not** write anything to the repository — Scope remains
write-less and source-less in the read sense.
