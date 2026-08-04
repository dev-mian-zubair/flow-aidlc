# Scope-phase sync report

Synced the reference PIP instance's Scope-phase enhancements (ticket-type
classification, epic decomposition, scope templates, Knowledge-Map grounding)
into the portable Flow package engine. Files only — no git commit, no worktree.

- SOURCE: `/home/codingcops/projects/Merge-20260603` (`.flow/`, `.claude/`)
- TARGET: `/home/codingcops/projects/personal/flow-aidlc/src/flow_aidlc/engine/`

## Files mapped

### New — templates + shared guide (created)
- `.flow/templates/scope/bug.tmpl.md`        → `engine/flow/templates/scope/bug.tmpl.md`
- `.flow/templates/scope/epic.tmpl.md`       → `engine/flow/templates/scope/epic.tmpl.md`
- `.flow/templates/scope/feature.tmpl.md`    → `engine/flow/templates/scope/feature.tmpl.md`
- `.flow/templates/scope/small-task.tmpl.md` → `engine/flow/templates/scope/small-task.tmpl.md`
- `.flow/steps/shared/knowledge-map.md`      → `engine/flow/steps/shared/knowledge-map.md`

(Created `engine/flow/templates/scope/` and `engine/flow/steps/shared/`.)

### Modified — step guides
- `engine/flow/steps/scope/clarify.md`  (classification + epic decomposition + Knowledge-Map grounding)
- `engine/flow/steps/scope/story.md`    (draft-from-template, epic parent+stubs, severity↔priority sync)
- `engine/flow/steps/scope/publish.md`  (epic parent+child creation, sub-issue linking; repo de-PIP'd)

### Modified — agents
- `engine/claude/agents/scope/scope-clarify.md`
- `engine/claude/agents/scope/scope-story.md`
- `engine/claude/agents/scope/scope-publish.md`

### Modified — command
- `engine/claude/commands/flow-scope.md`

### Config + playbook
- `engine/flow/config.tmpl.yaml` — added `tracker.create.ticket_types`,
  `priority_scheme`, `epic_children`, plus a top-level `knowledge:` block
  (`map_index`, `map_machine_index`). Existing `{{TOKENS}}` and comments intact.
- `engine/flow/playbook.md` — added the Scope-classification blockquote note
  after the per-stage table, before "## Checkpoint Rule".

## De-PIP applied (per rules)
- Repo `Perpetual-Intelligence/Merge-20260603` → "the tracker repo from
  `config.yaml` (`tracker.repo`)"; nowhere hardcoded.
- `PI-{n}` id-scheme form → "the configured id-scheme (`config.yaml` `id_scheme`)".
  `<PI-NNN>` worklog-dir placeholders kept generic to match the package's
  existing engine convention (used pervasively across shape/build/ship files).
- "System Map" wording → "Knowledge Map" (already the source's wording; verified none slipped in).
- GitHub-specific tool/field names generalized: `github-mcp-server`/`sub_issue_write`/
  `projects_write`/`list_issue_types`/`create_issue` → generic tracker MCP +
  "the tracker's sub-issue mechanism" + "board fields". The freshness shell
  command (`cd scripts/flow-checks && python3 -m flow_checks.freshness`) →
  described generically (git history vs `verified-at-sha`).
- Template PIP specifics genericized: `poc-1/2/3`, `pip-demo`, `PIP Delivery`,
  `Bug Dashboard`, `router`/`licensing` area lists, "migration token", version
  `1.11.0` → generic area/env/board wording.

Coupling sweep on all touched engine files (`Perpetual-Intelligence|Merge-20260603|
backend/app|System Map|PI-\{n\}`) → NOTHING. A broader scan (poc-N, pip-demo, PIP,
migration token, licensing, SpiceDB, Milvus, Alembic, etc.) also clean.

## Validation
- `config.tmpl.yaml` parses as YAML — OK.
- `pytest tests/ -q` → **74 passed**.
- Plugin regenerated (`flow_aidlc plugin build`): 10 commands, 14 agents, 7 hooks;
  `plugin/agents/scope-*.md` reflect the update; `plugin/.claude-plugin/plugin.json`
  valid JSON.
- End-to-end: `flow init --yes --repo acme/app --id-prefix ACME` into a fresh temp
  git repo. Confirmed `.flow/templates/scope/{bug,epic,feature,small-task}.tmpl.md`
  and `.flow/steps/shared/knowledge-map.md` exist; `.flow/config.yaml` contains
  `ticket_types` and `knowledge:`. `flow check <tmp>` → **gate PASSED, exit 0**
  (guardrail-lint, structure-check, freshness, reference-selfcheck all OK).

## CI note
The SOURCE also changed `.github/workflows/flow-checks.yml` and added
`knowledge-freshness.yml`. These were **intentionally not mapped** — the package
runs its gate via `flow check`, not PIP's CI. CI-blocking Knowledge-Map freshness
is a separate concern here; the package equivalent is `flow check` (freshness is
one of its checks) and a future `flow check --strict`.
