# ADR-blend + migration report

Removed all methodology-ADR references (0003, 0008, 0009, 0010, 0011) from the
shipped Flow engine, inlining each decision's essence into the surrounding prose.
A scaffolded consumer repo has no `knowledge/decisions/NNNN-*.md` files, so every
`decisions/NNNN` link and bare `ADR NNNN` mention was a dangling reference. Decision:
inline the rationale, ship no ADR files, add no new namespace.

## Part 1 — engine ADR references removed (30 → 0)

19 engine files edited under `src/flow_aidlc/engine/`:

- `claude/commands/flow-scope.md` — 0008 (invariants-only / no structural freshness)
- `claude/commands/flow-ship.md` — 0010 (Ship ends at open PR)
- `claude/commands/flow-refresh.md` — 0008 (structure in graph, not prose)
- `claude/agents/knowledge/curator.md` — 0008 ×2 (two-sources; freshness retired)
- `claude/agents/scope/scope-clarify.md` — 0008 (invariants-only maps)
- `claude/agents/shape/shape-map.md` — 0008 (maps hold invariants, not structure)
- `flow/steps/shape/design.md` — 0008 (structure in graph)
- `flow/steps/shape/map-existing.md` — 0008 (invariants/rationale a graph can't know)
- `flow/INTEGRATIONS.md` — 0008/0009 (graph owns structure; swappable via adapter)
- `flow/steps/ship/branch-hardening.md` — 0011, 0010 (independent epic branches; team's gate)
- `flow/README.md` — 0010 (terminal at open PR)
- `flow/templates/progress.tmpl.md` — 0011 (epic children are independent branches)
- `flow/templates/design.tmpl.md` — 0008 (structure in graph)
- `flow/playbook.md` — 0010 (team owns merge/checks/close)
- `flow/config.tmpl.yaml` — 0008/0009 (swappable graph adapter; Graphify default)
- `flow/steps/shared/knowledge-map.md` — 0008 ×2 (invariants; freshness retired)
- `flow/steps/ship/open-pr.md` — 0010 ×2, 0003, 0011 ×2 (worklog audit trail; base; epic branches)
- `flow/steps/shared/kickoff.md` — 0011 ×3, 0010 (branch at Shape entry; independent epic branches)
- `flow/steps/shared/graph.md` — 0008 ×2 (graph owns structure; swappable adapter)

### Per-ADR inline treatment (generic, de-PIP'd)

- **0003 (worklog-committed):** "the worklog is a committed part of the branch — the
  task's audit trail."
- **0008 (code-graph-owns-structure):** "structure comes from the code graph; the
  curated `knowledge/map/` docs hold only the invariants a graph can't know" (and the
  freshness-retired corollary where it appeared).
- **0009 (graph backend):** "Flow reaches the graph only through the graph adapter —
  the backend is swappable (Graphify by default)."
- **0010 (ship-ends-at-open-pr):** "the Ship phase ends at opening the PR — the team
  owns the merge, required checks, ticket close, and any lock release."
- **0011 (branch-creation-and-base):** "the branch is created at Shape entry (via
  `/flow-start`), off the configured base, before scaffolding the worklog; epic
  children are independent branches."

Preserved throughout: `config.*` references, the package's model frontmatter, and the
deliberate divergences (no re-hardcoded guardrail list, no `origin/main` literal, no
`make graph`, no PIP paths). The generic `knowledge/decisions/` *directory* mentions
(not ADR-numbered) were left intact.

### Grep-clean proof

```
$ grep -rInE "decisions/[0-9]{4}|ADR [0-9]{4}" src/flow_aidlc/engine   → (nothing; exit 1)
$ grep -rIlE "Perpetual-Intelligence|Merge-20260603|make graph|model: opus" src/flow_aidlc/engine   → (nothing; exit 1)
$ grep -rInE "decisions/[0-9]{4}|ADR [0-9]{4}" plugin/   → (nothing; exit 1)
```

## Part 2 — migration (source of truth)

- `README.md` Status: "Early — under active extraction…" → "**Source of truth for the
  Flow engine.** Extraction complete; package is canonical; reference instance frozen
  as historical reference; polish phase."
- `ARCHITECTURE.md`: no "under active extraction" text present — no change needed (it
  already states the engine is generic and shipped in this package).
- `docs/build-plan.md`: added a "## Migration (source of truth)" note at the top —
  M0–M6 complete, package canonical, PIP frozen as historical reference.

No ADR files created (the decision is to inline, not to ship ADRs).

## Part 3 — regression guard

Added `tests/test_no_dangling_adr_refs.py`: walks every file under
`src/flow_aidlc/engine/` with `pathlib`, asserts zero matches for
`decisions/[0-9]{4}` and `ADR [0-9]{4}`, listing any `file:line: match` offenders.

## Part 4 — regenerate + verify

- `flow plugin build` → rebuilt (10 commands, 15 agents, 6 hooks).
- `pytest tests/ -q` → **91 passed** (incl. the new test).
- `plugin/.claude-plugin/plugin.json` → valid JSON.
- Fresh `flow init --yes --repo acme/app --id-prefix ACME --base origin/main` then
  `flow check` → **gate PASSED**; grep of `<tmp>/.flow` + `<tmp>/.claude` for ADR refs
  → nothing.

Engine ADR refs = **0**.
