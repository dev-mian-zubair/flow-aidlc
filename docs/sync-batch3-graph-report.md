# Sync Batch 3 — Retire doc-freshness, adopt the code graph (Graphify)

Full-adoption sync of SOURCE commits `671a398e..c88565d9` (ADR 0008 code-graph-owns-structure
+ ADR 0009 adopt-graphify) from the PIP reference instance into the portable
`flow-aidlc` package. De-PIP'd throughout; package `model:` frontmatter preserved
(no `model: opus` imported).

## PART A — Freshness retired (deletions + rewiring)

Deleted:
- `src/flow_aidlc/checks/freshness.py`
- `tests/test_freshness.py`
- `src/flow_aidlc/engine/claude/hooks/freshness-flag.sh`

Rewired:
- `engine/claude/settings.json` — removed the `PostToolUse` block (its only hook was
  `freshness-flag.sh`); other hooks kept.
- `engine/manifest.yaml` — hooks are globbed (`claude/hooks/**`), no explicit
  freshness entry to remove.
- `commands/refresh.py` — repurposed: `flow refresh` now prints that structure
  freshness is graph-based, reads `config.yaml → graph.build`, offers to run it if the
  backend binary is on PATH (`subprocess.run` list form, honors `--dry-run`), else
  prints an install hint. Returns 0. Keeps the `find_repo_root` / "run flow init first"
  guard.
- `commands/check.py`, `cli.py`, `commands/init.py` — freshness wording updated;
  `--strict` documented as a compatibility no-op.

## PART B — Checks

- `checks/gate.py` — dropped the freshness check; gate now composes
  guardrail_lint + structure_check + reference-selfcheck + config_consistency (**4 checks**,
  labels renumbered to `/4`). `strict_freshness` kept for signature/CLI compatibility
  (ignored). Package's `find_repo_root` default preserved.
- `checks/config_consistency.py` — added **C6** (graph.backend must have a non-stub
  `### <backend>` mapping in `.flow/steps/shared/graph.md`) and **C7** (graph.root +
  every graph.focus dir must exist; graph.ignore_file if set must exist). Refactored C3
  to share a new `adapter_implements()` helper (matches SOURCE). C1/C2/C3/C5 kept; **C4
  remains intentionally omitted** (package de-hardcodes the guardrail echo).
- `tests/test_config_consistency.py` — fixture now scaffolds a graph adapter, a
  `graph:` config block, a `src/` focus dir, and `.graphifyignore`; added
  `test_c6_stub_backend_blocks`, `test_c7_missing_focus_dir_blocks`,
  `test_c7_missing_root_blocks`, `test_c7_missing_ignore_file_blocks`.

## PART C — Engine: graph adapter + config + rewiring

New / changed engine data:
- **NEW** `engine/flow/steps/shared/graph.md` — the universal code-graph adapter
  (backend=graphify), de-PIP'd (generic focus/ignore language; no PIP subsystem list).
- `engine/flow/config.tmpl.yaml` — added a `graph:` block with **fresh-init-safe
  defaults**: `focus: []`, `root: "."`, **no `ignore_file`** (documented as opt-in), so
  C7 passes on an empty repo.
- `engine/claude/mcp.tmpl.json` — servers now `github`, `context7`, `graphify`
  (removed postgres + playwright; graphify serves `graphify-out/graph.json` over stdio).

Engine markdown ported (content only, de-PIP'd, model preserved):
- `agents/knowledge/curator.md` — invariants-vs-structure split, `mcp__graphify` tool,
  freshness frontmatter retired.
- `agents/shape/shape-map.md` — graph-first (WHO_CALLS/NEIGHBORS/HUBS), `mcp__graphify`.
- `agents/scope/scope-clarify.md` — QUERY/HUBS structural grounding, `mcp__graphify`.
- `agents/build/build-verify.md` — removed `mcp__playwright`; artifact-sensor
  `--require` corrected to `## Steps,## Tests` (matches the package's code-plan
  template); checkpoint now points to `steps/ship/branch-hardening.md`.
- `commands/flow-refresh.md`, `commands/flow-scope.md`, `commands/flow-ship.md`.
- `steps/shape/map-existing.md`, `steps/shape/design.md`, `steps/scope/clarify.md`.
- `steps/build/verify.md` — Ship entry → `branch-hardening.md`.
- `steps/ship/branch-hardening.md` — added step 1b (IMPACT_OF_DIFF blast radius).
- `steps/shared/knowledge-map.md` — invariants framing, freshness section rewritten.
- `steps/shared/traceability.md` — corrected paths to `shape/requirements.md` /
  `shape/slices.md` (matches the package's `traceability.py`).
- `templates/design.tmpl.md` — Knowledge-map cross-check → invariants.
- `templates/progress.tmpl.md` — added `branch-hardening` under Ship.
- `templates/scope/feature.tmpl.md` — `type:feature` → `type:feat`.
- `templates/scope/small-task.tmpl.md` — reworded the automation flag note.

Skipped (PIP-specific / not-generic / not-present):
- `agents/review/checkpoint-reviewer.md`, `steps/shared/gotcha-checklist.md`,
  `steps/shape/requirements.md`, `.flow/playbook.md`, `progress.tmpl.md` guardrail
  list — the SOURCE deltas only add the PIP `dependency-provenance` guardrail / bump a
  hardcoded PIP guardrail count; the package already de-hardcodes these to
  "every enabled always-on guardrail", so nothing generic to port.
- `knowledge/map/*` thinning — the package ships knowledge/map EMPTY (scaffold), so
  map-thinning does not apply.
- `.flow/README.md`, `.flow/INTEGRATIONS.md` — the package does not ship these engine
  files (its team-setup lives in the root README + `flow doctor`), so there was no
  engine file to port into.

## flow-doctor (commands/doctor.py)

- Removed `freshness-flag.sh` from `_EXPECTED_HOOKS`.
- Replaced the "knowledge maps fresh" check with `_check_graph`: verifies
  `graph.backend` set + `graph.md` adapter present + reports whether the `graph.build`
  binary is on PATH + whether `graph.output` exists — **WARN, not FAIL**. Hooks check
  kept. Doctor exits 0 on a fresh init (graph WARN).

## PART D — Package docs

- `README.md` — freshness framing replaced with the code-graph model; added a
  **Prerequisites** section documenting Graphify alongside superpowers; quickstart adds
  `uv tool install "graphifyy[mcp]"` + `flow refresh`.
- `ARCHITECTURE.md` — new "Structure comes from the code graph (not prose)" section;
  command-surface + boundary tables updated; Graphify called out as a prerequisite.

## PART E — Plugin regenerated

`flow plugin build` → `plugin/`: commands 10, agents 15, **hooks 6** (was 7 —
freshness-flag.sh removed), version 0.1.0. All plugin JSON valid; no PostToolUse /
freshness hook; `flow-refresh` command reflects the graph rewire; plugin coupling clean.

## Acceptance results

- **No freshness left:** `grep freshness` in checks/hooks/tests → only `gate.py`'s
  incidental explanatory docstring (allowed); freshness.py / test_freshness.py /
  freshness-flag.sh deleted. `import freshness` → none.
- **Coupling clean:** `grep -E "Perpetual-Intelligence|Merge-20260603|backend/app|System Map|PI-{n}|model: opus"`
  over `src/flow_aidlc/engine` → none. Plugin → none.
- **Tests:** `pytest tests/ -q` → **88 passed** (test_freshness removed;
  config_consistency at 17 incl. the 4 new C6/C7 tests).
- **End-to-end:** fresh `flow init --yes --repo acme/app --id-prefix ACME` → `graph.md`
  present, config `graph:` block with `focus: []`, no `freshness-flag.sh` in
  `.claude/hooks/`. `flow check` → **gate PASSED, exit 0, 4 checks**. `flow doctor` →
  **exit 0** (graph WARN). `flow refresh --dry-run` reflects the graph rewire.

### Full gate output (fresh acme/app instance)

```
============================================================
CHECK 1/4  guardrail-lint
============================================================
OK

============================================================
CHECK 2/4  structure-check
============================================================
OK

============================================================
CHECK 3/4  reference-selfcheck
============================================================
OK: no reference cases (reference-runs/ not found)

============================================================
CHECK 4/4  config-consistency
============================================================
OK

gate PASSED
```

### flow doctor output (fresh acme/app instance)

```
[PASS] Flow present — .flow/ + playbook.md + config.yaml
[PASS] config valid — config parses; guardrail names resolve to files
[WARN] guardrails — no invariants authored yet — `flow guardrail add`
[PASS] hooks — 6 hooks present, executable, wired in settings.json
[WARN] graph — backend=graphify; adapter present; 'graphify' on PATH; graphify-out/graph.json not built yet — `flow refresh`
[PASS] git — .git present
[PASS] mcp — servers: context7, github, graphify

Verdict: OK
```
