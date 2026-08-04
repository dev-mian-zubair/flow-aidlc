# Build plan

Extract the Flow engine from the reference instance and ship it as a portable
package + CLI. Milestones are ordered so each ends with something runnable.

## M0 — Foundation (this commit)
- [x] Repo + package skeleton (`src/flow_aidlc/`), pyproject, README, ARCHITECTURE.
- [x] CLI dispatch (`flow <cmd>`) with subcommands wired (stubs where not yet built).

## M1 — Engine extraction (de-PIP-ify)
Bundle the generic engine assets under `src/flow_aidlc/engine/`, stripped of any
project-specific reference. Source: the reference instance's `.flow/`, `.claude/`,
`scripts/flow-checks/`.
- [ ] `engine/claude/{commands,agents,hooks}` + `settings.json` — copy as-is (already 0 project coupling), except:
      - `agents/review/guardrail-verifier.md` — replace the hardcoded 5 PIP guardrails with "load the always_on set from config.yaml".
      - `agents/scope/scope-publish.md` + `steps/scope/publish.md` — replace the hardcoded repo with `config.yaml tracker.repo`.
- [ ] `engine/flow/{playbook.md,steps,templates}` — copy generic guides; genericize:
      - `templates/requirements.tmpl.md` — the gotcha-checklist rows become generated from the active guardrail set (placeholder + `flow init` fills, or `flow guardrail add` regenerates).
      - `steps/shared/{gotcha-checklist,content-validation}.md` — strip PIP guardrail names; reference "the always_on set".
- [ ] `engine/flow/guardrails/optional/*` — genericize the 3 starters (security/resiliency/test-coverage) to be CI-agnostic (they currently cite PIP CI paths).
- [ ] `engine/flow/guardrails/always-on/` — ship EMPTY + a `TEMPLATE.md` + a `README.md` ("author your invariants here").
- [ ] `engine/flow/config.tmpl.yaml`, `engine/flow/knowledge-map.tmpl.yaml` — `init`-filled templates.
- [ ] `engine/knowledge/{map/README.md,decisions/README.md,practices.md}` — scaffolds.
- [ ] A `manifest.yaml` marking each shipped path `engine` or `instance` (drives `upgrade`).

## M2 — `checks/` (the gate, generalized)
- [ ] Vendor the `flow_checks` modules (guardrail_lint, structure_check, freshness, traceability, learnings, scorer, reference_check, artifact_sensor, gate) into `flow_aidlc/checks/` — they are already project-agnostic; adjust only path assumptions (repo root discovery).
- [ ] `flow check` / `flow selftest` / `flow refresh` call them against the target repo's `.flow/`.
- [ ] Port the tests.

## M3 — `flow init` (the flagship)
- [ ] Interactive prompts: tracker (github/jira/linear), repo slug, id-scheme, detected stack.
- [ ] Copy `engine/*` → target `.flow/`, `.claude/`, `knowledge/`; generate `config.yaml` + `knowledge-map.yaml` from answers.
- [ ] Merge (not clobber) `.claude/settings.json`; install git hooks; add `.gitignore` entries; append a "The Flow" pointer to the host `CLAUDE.md` (create if absent).
- [ ] Idempotent + `--dry-run`; refuse to overwrite an existing instance without `--force`.
- [ ] Acceptance: `flow init` into a temp git repo → `flow check` exits 0.

## M4 — authoring helpers
- [ ] `flow guardrail add <name>` — scaffold from `TEMPLATE.md`, register in config, regenerate the requirements checklist rows.
- [ ] `flow map add <glob> <doc>` — scaffold a map doc with provenance frontmatter + wire knowledge-map.yaml.
- [ ] `flow doctor` — hooks installed? structure valid? MCP configured? (generalize `flow-doctor.sh`).

## M5 — `flow upgrade` + packaging
- [ ] `flow upgrade` — replace engine files by manifest, never touch instance files; bump `.flow/VERSION`.
- [ ] Publish to PyPI (`flow-aidlc`); a `flow --version` self-check.

## M6 — Claude Code plugin
- [ ] Wrap `.claude/*` as a plugin (marketplace manifest); the plugin's `/flow-init` shells to the CLI.

## Notes
- The reference instance lives at `/home/codingcops/projects/Merge-20260603` (read-only source for extraction).
- Keep the engine's `superpowers:*` skill references — Flow is powered by superpowers; document it as a prerequisite.
