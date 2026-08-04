---
status: FRESH
verified-at-sha: 0000000
---

# Knowledge Map Index

This directory contains descriptive maps of **your project's** key subsystems.
Each map carries provenance frontmatter (`status`, `derives-from`,
`verified-at-sha`) that drives the freshness loop — when code under
`derives-from` changes, the map is flagged STALE by `freshness-flag.sh` (WS-4)
and queued for re-derivation by the `curator` agent (WS-7).

Maps are **descriptive** (what a subsystem is) and **concise** (≤ 1 screen).
They are never prescriptive — decisions live in `knowledge/decisions/`.

## Maps

This table starts empty. Add a map with `flow map add <doc> <glob>...`, which
creates `knowledge/map/<doc>.md` and records its `derives-from` globs in
`.flow/knowledge-map.yaml`. Then add a row here:

| Document | What it covers | derives-from |
|---|---|---|
| _(none yet — `flow map add` populates this)_ | | |

## Machine index

`.flow/knowledge-map.yaml` is the machine-readable version of this table,
consumed by `freshness-flag.sh` and `freshness.py`.
