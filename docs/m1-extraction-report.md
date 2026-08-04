# M1 — Flow engine extraction report

Extracted the generic Flow engine from the reference PIP instance
(`/home/codingcops/projects/Merge-20260603`) into the portable package at
`src/flow_aidlc/engine/` (layout: `flow/`, `claude/`, `knowledge/`).

**No git commit was made** — the parent commits after review.

## Result

- **Engine file count:** 82 files under `engine/`.
- **Required residual-coupling grep:** clean — NO hits for
  `Perpetual-Intelligence|backend/app|require_entitlement|budgets table|router.system_enabled|spicedb|SpiceDB`.
- **Parse checks:** `config.tmpl.yaml`, `knowledge-map.tmpl.yaml`,
  `manifest.yaml` (YAML) and `mcp.tmpl.json` (JSON) all parse.
- **Hooks:** all 8 `claude/hooks/*.sh` remain executable (`-rwxrwxr-x`).

## Step 1 — Clean assets copied verbatim

`cp`/`cp -r` with structure preserved:

- `.flow/playbook.md`, `.flow/VERSION` → `flow/`
- `.flow/steps/**` (entire tree), `.flow/templates/**` (entire tree)
- `.flow/guardrails/optional/**`
- `.claude/commands/**`, `.claude/agents/**`, `.claude/hooks/**` (executable
  preserved), `.claude/settings.json`
- `knowledge/map/README.md`, `knowledge/decisions/README.md`,
  `knowledge/practices.md`

(Several of these were then edited in Steps 4–5 in the target.)

## Step 2 — Config → init-fillable templates (PIP values NOT copied)

- `flow/config.tmpl.yaml` — tokenized `tracker.repo` → `{{TRACKER_REPO}}`,
  `tracker.platform` → `{{TRACKER_PLATFORM}}` (default github),
  `tracker.mcp` → `{{TRACKER_MCP}}`, `id_scheme` → `{{ID_PREFIX}}-{n}`.
  **`guardrails.always_on: []` (EMPTY)** per spec; kept
  `optional: [security-baseline, resiliency-baseline, test-coverage]`. Schema
  and comments retained. Placeholder scalar values are quoted so the template
  is valid YAML.
- `flow/knowledge-map.tmpl.yaml` — `maps: []` with a comment explaining
  `flow map add` populates it.
- `claude/mcp.tmpl.json` — from `.mcp.json`. Kept `github` (env `GITHUB_TOKEN`)
  and `context7` active; moved `postgres` (DSN → `{{FLOW_DB_READONLY_URI}}`) and
  `playwright` into a disabled/commented `_disabled` block with enable notes
  (JSON has no native comments).

## Step 3 — Empty always-on guardrails dir with authoring aids

Did NOT copy the 5 PIP always-on guardrails. Created:

- `flow/guardrails/always-on/README.md` — explains always-on guardrails are the
  project's own blocking invariants, one per invariant, checked by
  `guardrail-verifier`, must cite real repo code; references
  `flow guardrail add <name>`.
- `flow/guardrails/always-on/TEMPLATE.md` — generic skeleton mirroring the real
  guardrail section structure (`## Rule`, `## Verification` with
  `**<PREFIX>-01**` ids, `## Blocks on`, `## Powered by superpowers`) with
  `[FILL]` placeholders. No PIP content.

## Step 4 — De-PIP-ified coupled files (edited in target)

- `flow/playbook.md` — replaced the enumerated 5 PIP always_on guardrails with
  "whatever your `config.yaml` lists — empty until you author guardrails"
  (kept the generic optional list); also fixed line 13 "all five always-on
  guardrails" → "every enabled always-on guardrail in `config.yaml`".
- `flow/steps/shared/gotcha-checklist.md` — rewritten generically: one row per
  always-on guardrail in `config.yaml`; a project with none has an empty
  checklist. Removed the 5 PIP invariant rows/links.
- `flow/templates/requirements.tmpl.md` — replaced the 5 PIP checklist rows with
  a single `[Answer]:` placeholder row + comment
  (`<!-- one row per always-on guardrail in config.yaml; flow guardrail add regenerates these -->`).
  Section header, SNAPSHOT header, FR/NFR/Intent untouched.
- `flow/steps/shared/content-validation.md` — genericized the one PIP citation
  example (`backend/app/services/budget/_core.py:142` → `src/services/orders.py:142`);
  all generic validation rules kept.
- `flow/steps/scope/publish.md` — replaced hardcoded repo
  `Perpetual-Intelligence/Merge-20260603` (3 occurrences) and `mcp: github`
  with references to `config.yaml tracker.repo` / `tracker.mcp`.
- `claude/agents/scope/scope-publish.md` — same repo de-hardcode → `config.yaml
  tracker.repo`; "github MCP" → "tracker MCP".
- `claude/agents/review/guardrail-verifier.md` — removed the hardcoded 5-guardrail
  enumeration and the PIP-specific guardrail-reference block; now instructs to
  load the enabled set from `config.yaml` (`always_on` + enabled `optional`) and
  not hardcode a list; genericized the output-format example rows (SEC/RES/TEST
  instead of MIG/BUD/AUTHZ); dropped "for PIP". Read-only stance kept.

Additional low-risk branding removals (portability): dropped "for PIP" from
`build-generate`, `build-plan`, `build-verify`, `checkpoint-reviewer`,
`curator` agents and from `claude/hooks/_lib.sh`.

`knowledge/map/README.md` (an instance seed) contained a PIP-specific map table;
rewrote it to a generic index with an empty maps table + `flow map add` guidance.

## Step 5 — Genericized the 3 optional guardrails

`security-baseline.md`, `resiliency-baseline.md`, `test-coverage.md` (+ their
`*.ask.md` opt-in files): kept the rule intent, `## Rule`/`## Verification`
structure, and SEC/RES/TEST ids. Replaced PIP CI/tool specifics
(`.github/workflows/ci.yml`, bandit, gitleaks, `safe_http`, the bare-except file
list, `backend/tests/`, `pytest --cov`/`interrogate`, Milvus/SpiceDB/MinIO/Celery
paths) with CI-agnostic wording ("your CI's secret-scan / SAST / SSRF / coverage
step, if configured; otherwise a review-time check"). Still useful as starters.

## Step 6 — Manifest

`engine/manifest.yaml` — `{ engine: [...], instance: [...] }`. Everything is
`engine` except the instance seeds: `flow/config.tmpl.yaml`,
`flow/knowledge-map.tmpl.yaml`, `claude/mcp.tmpl.json`,
`flow/guardrails/always-on/**` (README + TEMPLATE listed as engine exceptions),
`knowledge/map/**` (README = engine), `knowledge/decisions/**` (README = engine),
`knowledge/practices.md`. Comment notes more-specific `engine` globs win over
broader `instance` ones.

## Concerns (out of the named scope)

The required residual-coupling grep is clean and all Step-4/5 named files were
de-PIP-ified. A broader sweep surfaced coupling in files **not** listed in the
task's edit set, left intentionally to avoid scope creep and touching
load-bearing semantics:

- `flow/steps/ship/release-checklist.md` and `flow/steps/ship/handoff.md`
  hardcode PIP release mechanics: `make backend-test` / `make frontend-build` /
  `make frontend-typecheck`, `alembic heads` single-head check,
  `worklog/MIGRATION-LOCK.md`, and the `pip-release` runbook. These overlap with
  the removed migration-safety guardrail and the Makefile-based CI, so
  genericizing them is a follow-up rather than part of this extraction.
- These do not trip the required residual grep (no `backend/app`, etc.).

## Validation commands run

- `find engine -type f | sort` — 82 files, layout correct.
- Required grep — NO hits.
- `python3` YAML/JSON parse of the 3 YAML + 1 JSON template — all OK (needed to
  quote the `{{...}}` scalar values in `config.tmpl.yaml` so it stays valid YAML).
- Hooks confirmed executable.

## M1b de-PIP completion

Completed the de-specialization sweep — genericized 9 engine files still carrying
PIP-specific details. Edits confined to `src/flow_aidlc/engine/`.

- **`flow/config.tmpl.yaml`** — added a `commands:` block (test/build/lint/typecheck
  as `{{TEST_CMD}}` etc.) so a project declares its own shell commands via `flow init`.
- **`flow/steps/build/verify.md`** — replaced `make backend-test` / `npm run test`
  with a reference to `config.yaml` → `commands.test`; removed the hardcoded PIP
  always-on guardrail list (`migration-safety`, `budget-integrity`, `router-safety`,
  `license-sku-gating`) in favor of "config is the single source of truth" + generic
  `<guardrail-name>` result rows.
- **`flow/steps/build/generate.md`** — final-suite step now points to `commands.test`.
- **`claude/agents/build/build-generate.md`** — full-suite step now points to `commands.test`.
- **`claude/agents/build/build-verify.md`** — tests step points to `commands.test`;
  guardrail result example rows genericized to `<guardrail-name>`.
- **`flow/steps/ship/release-checklist.md`** — rewrote the checklist generically:
  test/build/lint/typecheck from `config.yaml commands.*` + "CI is green"; replaced
  the Alembic single-head + `MIGRATION-LOCK.md` lines with a generic conditional
  ("if your project uses a coordination lock, release it on merge"); replaced the
  `pip-release` runbook hand-off with "follow your project's release/deploy procedure,
  if any". Checkpoint + structure preserved.
- **`flow/steps/ship/handoff.md`** — migration-lock release step is now a generic
  coordination-lock conditional (both step 2 and the Output line); INDEX update,
  ticket close, and final journal entry kept.
- **`claude/agents/review/guardrail-verifier.md`** — read-only-bash example `alembic heads`
  replaced with `git diff HEAD` / read-only inspection commands.
- **`flow/steps/scope/publish.md`** — `PI-{n}` identifier → the configured id-scheme
  identifier (`config.yaml` → `id_scheme`); kept "(the tracker issue number)".
- **`flow/steps/shared/decision-log.md`** — the "single Alembic head" example log line
  replaced with a generic test-coverage decision; line format and other examples kept.

**Validation:**
- Coupling sweep re-run — clean (grep exit 1, no matches).
- `config.tmpl.yaml` parses under `yaml.safe_load`.
- Each edited `.md` step doc has exactly one H1; the three `claude/agents/*` files
  use YAML frontmatter (no H1) as before — structure preserved.
