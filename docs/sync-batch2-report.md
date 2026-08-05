# Flow sync — batch 2 (reference `058fa146..HEAD`, 13 commits) → portable package

De-PIP'd port of the newer Flow methodology into `flow-aidlc`. Files written only;
no git commit. Test venv: `scripts/flow-checks/.venv/bin/python` (pytest + pyyaml).

## PART A — check modules (code)

| Item | Action |
|---|---|
| `checks/config_consistency.py` | **Vendored.** Imports `flow_checks.` → `flow_aidlc.checks.`; root discovery via `_root.find_repo_root` (matches gate/freshness). **Adapted for package design:** C1 now skips `README.md` / `TEMPLATE.md` (engine authoring aids that live in `guardrails/always-on/`); **C4 (guardrail-echo) dropped** — the package intentionally de-hardcodes the always_on list in its prose (guardrail-verifier / playbook / build-verify treat `config.yaml` as sole source of truth), so there is no prose echo to protect and C4 would break every `guardrail add`. C1/C2/C3/C5 retained. |
| `tests/test_config_consistency.py` | **Vendored** (already tmp-fixture based, repo-independent). Imports rewritten; the C4 test removed with an explanatory note; 13 tests. |
| `checks/gate.py` | **Delta applied** (not overwritten): composes `config_consistency` as CHECK **5/5** "config-consistency" (blocking); all `N/4` → `N/5`. |
| `checks/freshness.py` | **Delta applied**: `_git_log_range` now returns `None` on git error (unresolvable / GC'd `verified-at-sha`); caller treats `None` as STALE rather than silently fresh. |

## PART B — new engine files (de-PIP'd)

- `claude/agents/shape/shape-research.md` — `model: sonnet` (matches package shape agents).
- `flow/steps/shape/research.md`
- `flow/templates/research.tmpl.md`
- `flow/steps/shared/tracker.md` — tracker adapter (github implemented; jira/linear NOT IMPLEMENTED stubs). Critical for C3.
- `flow/steps/ship/branch-hardening.md`
- `flow/guardrails/optional/dependency-provenance.md` — shipped as **optional** (PIP runs it always-on); kept DEP-* ids + `## Rule` / `## Verification`; genericized manifests + CI check names; added a note that a project may promote it to always-on.
- `flow/guardrails/optional/dependency-provenance.ask.md` — opt-in stub matching the other `*.ask.md` files.

De-PIP applied throughout: repo literal removed (adapter reads `config.tracker.repo`); `PI-{n}` scheme not hardcoded; worklog dirs `<ID>-NNN`; governance/CI names generic; "Knowledge Map" preserved.

## PART C — modified engine files

**Ported (real content change, package `model:` preserved):**

- Steps: `scope/publish.md` (adapter ops `DEDUP_SEARCH`/`CREATE_TICKET`/`ADD_SUB_ISSUE`/`SET_FIELDS`), `shape/map-existing.md` (seeded-survey reframe, seeds from Knowledge Map), `shape/requirements.md` (+research constraint bullet), `shape/design.md` (dependency adoption is cross-cutting), `build/code-plan.md` (flag dep-adding checkboxes with dependency-provenance guardrail marker), `shared/kickoff.md` (verify ticket exists / route to `/flow-scope`), `ship/handoff.md` (`CLOSE`/`COMMENT` adapter), `ship/release-checklist.md` (`OPEN_PR`/`COMMENT` adapter).
- Agents: `scope/scope-clarify` (tracker adapter ref), `scope/scope-publish` (CREATE_TICKET adapter), `shape/shape-intake` (verify-ticket + research routing + `mcp__github` tool), `shape/shape-map` (seeded-survey), `review/guardrail-verifier` (added `dependency-provenance (DEP)` to the **optional** list — not the hardcoded always_on the reference uses).
- Commands: `flow-start.md` (gate on a verified ticket, auto-chain to `/flow-scope`, conditional research pre-step), `flow-ship.md` (branch-hardening first).

**Skipped — model-only (no content change):** `scope-story`, `shape-design`, `shape-requirements`, `shape-slice`, `build-plan`, `build-generate`, `build-verify`, `curator`, `checkpoint-reviewer`.

**Skipped — PIP-specific, package already generic:**

- `steps/build/verify.md` — reference delta only appends `dependency-provenance` to a **hardcoded** always-on list; the package deliberately removed that hardcoded list ("Do not hardcode a guardrail list here"). No port.
- `templates/requirements.tmpl.md` — reference adds a row to a hardcoded PIP invariant table; the package uses a generic placeholder (`one row per always-on guardrail in config.yaml`). Preserved the generic placeholder; no port.

## PART D — config.tmpl + playbook

- `config.tmpl.yaml`: added `dependency-provenance` to `guardrails.optional` (kept `always_on: []`); added the `review.branch_hardening` block (5 pr-review-toolkit agents).
- `playbook.md`: added two stage rows — `Shape / research` (CONDITIONAL, `deep-research`, checkpoint) in the Shape block; `Ship / branch-hardening` (ALWAYS, `pr-review-toolkit` agents, checkpoint) before `handoff` in the Ship block. Generic always_on prose preserved.

## PART E — plugin regenerated

`flow_aidlc plugin build` → commands: 10, agents: **15** (was 14; +shape-research), hooks: 7.
`plugin/agents/shape-research.md` present; `plugin/.claude-plugin/plugin.json` valid JSON.

## Acceptance

- **Coupling sweep** `grep -rIlE "Perpetual-Intelligence|Merge-20260603|backend/app|System Map|PI-\{n\}|model: opus" src/flow_aidlc/engine` → **nothing** (exit 1). `model: opus` not imported. Plugin also clean.
- **Tests** `PYTHONPATH=src pytest tests/ -q` → **87 passed** (74 pre-existing + 13 config_consistency).
- **End-to-end** fresh init (`init --yes --repo acme/app --id-prefix ACME`) then `flow check`:

```
============================================================
CHECK 1/5  guardrail-lint
============================================================
OK

============================================================
CHECK 2/5  structure-check
============================================================
OK

============================================================
CHECK 3/5  freshness
============================================================
OK: all docs are up to date

============================================================
CHECK 4/5  reference-selfcheck
============================================================
OK: no reference cases (reference-runs/ not found)

============================================================
CHECK 5/5  config-consistency
============================================================
OK

gate PASSED
```

  Exit 0. C1 optional includes `dependency-provenance` (matching rule file); C2 no repo literal (`acme/app`); C3 github mapping in `tracker.md`; C4 not applicable (always_on `[]` + not vendored); C5 branch_hardening agents echoed in `branch-hardening.md`.
- New files present in fresh init: research.md, tracker.md, branch-hardening.md, research.tmpl.md, dependency-provenance.md — all OK.
- Plugin: `plugin/agents/shape-research.md` present; `plugin.json` valid.

## Deviations from the brief

1. **C4 not vendored** — incompatible with the package's de-hardcoded always_on design (would break `guardrail add`). C1/C2/C3/C5 vendored.
2. **C1 skips README.md / TEMPLATE.md** — the package ships these as engine authoring aids in `guardrails/always-on/`; without the skip the fresh-init gate fails on them.
3. **verify.md and requirements.tmpl.md content NOT ported** — the reference deltas only extend hardcoded PIP lists the package intentionally removed / genericized.
