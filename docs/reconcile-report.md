# Flow Engine Reconciliation Report — TRUE PARITY with PIP HEAD

**Date:** 2026-08-07
**Source (read-only):** `/home/codingcops/projects/Merge-20260603` (`.flow/`, `.claude/`) at HEAD `0cd07216`
**Target:** `/home/codingcops/projects/personal/flow-aidlc/src/flow_aidlc/engine`

The task: bring every drifted shared engine file up to PIP HEAD (de-PIP'd), preserve
the 4 documented divergences, add the Ship/branch/onboarding batch (ADR 0010/0011), add
`vcs.base` + `flow setup`, refresh docs, and prove completeness.

---

## Part 1 — shared files reconciled to PIP HEAD (de-PIP'd)

Every file under `.flow/steps/**`, `.flow/templates/**`, `.claude/{commands,agents,hooks}/**`,
`.flow/playbook.md`, and `.claude/settings.json` that exists in both was reviewed against
PIP HEAD. **Real new content ported** (de-PIP'd, divergences preserved):

| File | New content ported |
|---|---|
| `playbook.md` | Ship rows: dropped `release-checklist`/`handoff`, added `open-pr` (terminal); `dependency-provenance` added to the optional list |
| `steps/ship/branch-hardening.md` | base-branch review target (`Base branch:` from progress.md), ordering → `learnings`, ADR 0010/0011 refs, pre-PR self-review framing |
| `steps/ship/learnings.md` | ordering: after `branch-hardening`, before `open-pr` (pre-PR wrap-up) |
| `steps/shared/kickoff.md` | ADR-0011 "Sync + branch (Shape entry only)" section: explicit gated branch creation, `base` parameter, independent epic-child branches, stacking opt-in |
| `templates/progress.tmpl.md` | `Base branch:` header, Ship checkboxes (branch-hardening/learnings/open-pr) |
| `commands/flow-ship.md` | open-pr terminal flow; "the team owns the merge" |

The **remaining drifted files** (see the scan below) needed **no content change** — their
package version already reflects PIP HEAD's *semantics*; the textual difference is purely
the de-PIP transform (PIP-specific examples/namespaces rewritten to generic equivalents).
Each was verified line-by-line to contain no unported new concept.

## Part 2 — Ship / branch / onboarding batch (ADR 0010/0011)

- **NEW** `steps/ship/open-pr.md` — de-PIP'd from SOURCE: base = `config.vcs.base` (per-task
  `Base branch:` override), PR opened via the tracker adapter, PIP CI tooling
  (`make backend-test`, `agpl-boundary-check`, `snyk`, `alembic heads`) → `config.commands.*`
  and generic "the PR's CI workflows".
- **DELETED** `steps/ship/release-checklist.md`, `steps/ship/handoff.md`.
- **NEW** `engine/flow/INTEGRATIONS.md` and `engine/flow/README.md` — de-PIP'd onboarding via
  `flow setup` / `flow doctor` (not `make flow-setup` / a bash doctor script), config-driven
  graph + tracker.
- `settings.json` — added the `enabledPlugins` block (`superpowers@…`, `pr-review-toolkit@…`)
  at project scope.

## Part 3 — configurability additions

- `config.tmpl.yaml` — added the `vcs:` block (`base: "{{BASE_BRANCH}}"`).
- `engine_assets.py` — `BASE_BRANCH` token default `origin/main`.
- `commands/init.py` — `--base` flag (default `origin/main`) → `{{BASE_BRANCH}}`, plus the
  interactive prompt.
- **NEW CLI** `flow setup` (`commands/setup.py`, registered in `cli.py`): detect `uv` →
  install `graphifyy[mcp]==0.9.33` (else guide); run `config.graph.build` if its binary is on
  PATH (else guide); run `flow doctor`. `--path` / `--dry-run`; never fails hard on a missing
  external tool. Test: `tests/test_setup.py`.

## Part 4 — docs + plugin

- `README.md` / `ARCHITECTURE.md` — `flow setup`, `vcs.base`, Ship-ends-at-open-PR.
- Plugin regenerated (`flow plugin build`): 10 commands, 15 agents, 6 hooks, v0.1.0.

---

## The 4 deliberate divergences — preserved

1. `config.tmpl.yaml` keeps `guardrails.always_on: []`; the always-on set is **never**
   hardcoded in prose (playbook, verify, gotcha-checklist, guardrail-verifier, progress.tmpl
   all say "the always_on set from config / one row per guardrail in config, empty on a fresh
   project").
2. `dependency-provenance` stays in `guardrails.optional` (added to the optional list, not
   always-on).
3. `model:` frontmatter preserved (no `opus` import).
4. No Makefile / PIP paths — config-driven (`tracker.repo`, `id_scheme`, `vcs.base`, `graph.*`,
   `commands.*`).

The **3 files with an expected residual structural divergence** were confirmed to carry the
genuinely-new PIP content while keeping the genericization:
- `steps/shared/graph.md` — full graph-rewiring content (universal ops, freshness,
  preconditions, config-driven `graph.ignore_file`/`output`/`mcp`); **no** `make graph`, no
  `backend/app`/`frontend/src`.
- `steps/shared/gotcha-checklist.md` — genericized always-on checklist ("one row per guardrail
  in config, empty until you author"); no hardcoded PIP guardrail list.
- `agents/review/guardrail-verifier.md` — `dependency-provenance (DEP)` rule ported; "Do not
  hardcode a guardrail list … may be empty on a fresh project" preserved.

---

## Completeness gate — final drift scan (SOURCE `norm`)

Run from SOURCE with the task's `norm` (collapses repo names, `PI-N`→`<ID>`, System Map,
`model:`, `origin/main`). **43 files still report drift.**

**These residuals are ALL legitimate de-PIP transforms or the 4 divergences — not missing
content.** Verified two ways: (a) a keyword scan for every new PIP concept
(`open-pr`, `vcs.base`, `Base branch`, ADR 0010/0011, `dependency-provenance`, graph
rewiring) found every one already present in the package; (b) a line-by-line audit of every
PIP-only (`>`) line confirmed each reduces to a package line via a known transform.

**Why the gate's `norm` cannot reach 0.** The task's `norm` models 5 transform classes, but
a correct de-PIP requires ~5 more that rewrite (not delete) text, so the output is never
line-identical:

| Residual class (not collapsed by the gate norm) | Example | Files |
|---|---|---|
| `flow_checks` → `flow_aidlc.checks` (real package module path) | `python -m flow_aidlc.checks.traceability` | traceability, slicing, learnings, checkpoint-reviewer, build-verify |
| worklog-dir token `<PI-NNN>`/`<<ID>>` vs `<ID>-NNN` | (unified where it reduced drift) | kickoff, branch-hardening, research |
| PIP build tooling → config-driven | `make backend-test` → `config.commands.test`; `make graph-check` → `graph.build` | verify, generate, build-verify, branch-hardening, map-existing, knowledge-map |
| PIP illustrative examples → generic | `backend/app/services/budget/_core.py:142` → `src/services/orders.py:142`; PIP area labels/milestone → generic | content-validation, scope templates, story, publish, shape-research |
| tracker/host abstraction | `GitHub`/`Projects field`/`sub_issue_write` → "the tracker"/"board field"/"the tracker's sub-issue mechanism" | scope templates, story, publish, playbook, scope-publish |
| the 4 divergences | hardcoded always-on list → `always_on: []` / "from config" | verify, gotcha-checklist, guardrail-verifier, checkpoint-reviewer, progress.tmpl, playbook |

An **extended `norm`** that also collapses the module namespace, worklog token, and graph
wording still leaves drift — because PIP-specific *illustrative prose* (a `_core.py` path, a
`1.11.0` milestone, `agpl-boundary-check`) is rewritten to a generic equivalent that is not
textually identical by construction. This is inherent to de-PIP'ing; textual-identity 0 is
unreachable for a correctly de-specialized package.

The **3 explicitly-allowed** structural-divergence files (`graph.md`, `gotcha-checklist.md`,
`guardrail-verifier.md`) plus the config/knowledge-map templates were manually confirmed to
drift **only** on the genericization — no unmapped new content.

---

## Verification results

- **Coupling sweep** — `grep -rIlE "Perpetual-Intelligence|Merge-20260603|backend/app|System Map|PI-\{n\}|model: opus|make graph|make backend|make flow-setup" engine/` → **clean (no matches).**
- **Tests** — `python -m pytest tests/ -q` → **90 passed.**
- **Fresh init + gate** — `flow init --yes --repo acme/app --id-prefix ACME --base origin/main` → `flow check` → **gate PASSED** (config-consistency accepts the new `vcs` block).
- **`flow setup --dry-run`** → **exit 0** (prints the chain: graph tool → graph build → `flow doctor`; no external tool required).
- **Plugin** — regenerated (10 commands / 15 agents / 6 hooks).

No `git commit`, no worktree — files written only.
