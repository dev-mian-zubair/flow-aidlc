# M3 — `flow init` implementation report

## Summary

Implemented the flagship `flow init` command that scaffolds a Flow instance into
a target repo, plus its token-rendering helper. End-to-end (`flow init` →
`flow check`) passes: **gate PASSED, exit 0**, with no `{{TOKEN}}` placeholders
left in the generated `.flow/config.yaml` or `.mcp.json`.

## Files

- `src/flow_aidlc/engine_assets.py` (new) — `engine_dir()`, `TOKEN_DEFAULTS`,
  `render()`. Deterministic regex token substitution (`{{TOKEN}}` →
  `values.get(TOKEN, "")`); no eval.
- `src/flow_aidlc/commands/init.py` (replaced the `staged()` stub) — the full
  `run(argv) -> int` command.
- `tests/test_init.py` (new) — 3 tests.
- `src/flow_aidlc/checks/guardrail_lint.py` (one-line fix) — the lint now skips
  the always-on authoring aids `README.md` and `TEMPLATE.md` (same spirit as the
  existing `*.ask.md` skip). Without this the gate failed on the engine-shipped
  `guardrails/always-on/README.md`, which is prose, not an enforceable
  guardrail. See "Concern / decision" below.

## The init flow

Target = `--path` or cwd. Guards: refuse if `.flow/` exists without `--force`
(prints the required message, returns 1); warn (don't fail) if not a git repo.

Values start from `TOKEN_DEFAULTS`, overridden by flags
(`--tracker`→PLATFORM+MCP, `--repo`→TRACKER_REPO, `--id-prefix`→ID_PREFIX,
`--test-cmd`/`--build-cmd`/`--lint-cmd`/`--typecheck-cmd`, `--db-uri`). Interactive
prompts only when stdin is a TTY and not `--yes`.

Scaffold (all no-ops under `--dry-run`, which prints each planned action):

1. `engine/flow/` → `target/.flow/` verbatim, skipping `config.tmpl.yaml` and
   `knowledge-map.tmpl.yaml` (rendered separately). Artifact templates
   (`flow/templates/*.tmpl.md`) copied verbatim; guardrails and subdirs
   preserved.
2. `engine/claude/` → `target/.claude/`, skipping `mcp.tmpl.json` and
   `settings.json`. Copied `*.sh` hooks re-`chmod +x`.
3. `engine/knowledge/` → `target/knowledge/`.
4. Render `config.tmpl.yaml` → `.flow/config.yaml`.
5. Render `knowledge-map.tmpl.yaml` → `.flow/knowledge-map.yaml`.
6. Render `mcp.tmpl.json` → `target/.mcp.json` (repo ROOT).
7. Ensure `target/worklog/` exists.
8. `settings.json` merge: copy if absent; else deep-merge engine hooks per event
   key without duplicating an identical command, preserving the user's keys;
   pretty JSON (indent=2).
9. `.gitignore`: append `worklog/.active` and `.superpowers/` if missing.
10. `CLAUDE.md`: append a "## The Flow" pointer section (create minimal file if
    absent) unless `.flow/playbook.md` is already mentioned.
11. `.flow/VERSION`: left as the copied engine value (backfilled to
    `__version__` only if somehow absent).

Prints a success summary (target, tracker/id-prefix, created dirs, Next Steps:
`flow doctor`, `flow check`, `/flow-scope`) and returns 0.

## Test results

`PYTHONPATH=src <venv> -m pytest tests/ -q` → **61 passed** (58 pre-existing + 3
new init tests). No failures, no regressions.

New tests:
- `test_init_scaffolds_and_gate_passes` — git-init tmp, run init, assert
  `.flow/config.yaml` contains `owner/name` and `PI-{n}` with no `{{` left; core
  files exist (`playbook.md`, `.claude/commands/`, `session-start.sh`,
  `knowledge/map/README.md`, `.mcp.json`); `.gitignore` has `.superpowers/`;
  then `gate.run(tmp_path) == 0`.
- `test_init_refuses_existing_without_force` — 0, then 1 (no force), then 0
  (with `--force`).
- `test_init_dry_run_writes_nothing` — returns 0 and `.flow/` absent.

## End-to-end gate output

Command: fresh tmp dir, `git init`,
`flow init --yes --repo acme/app --id-prefix ACME --path <tmp>`, then
`cd <tmp> && flow check`:

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
CHECK 3/4  freshness
============================================================
OK: all docs are up to date

============================================================
CHECK 4/4  reference-selfcheck
============================================================
OK: no reference cases (reference-runs/ not found)

gate PASSED
EXIT=0
```

`id_scheme` rendered to `ACME-{n}`; `tracker.repo` to `acme/app`. No `{{` tokens
remain in `.flow/config.yaml` or `.mcp.json`. Hooks executable; `settings.json`
valid with all 7 hook events; `CLAUDE.md` carries the Flow pointer.

## Concern / decision

`guardrail_lint` recurses the whole guardrails tree, so it lints the
engine-shipped `guardrails/always-on/README.md` (prose) and `TEMPLATE.md`
(fill-in scaffold). The manifest classifies both as engine authoring aids, and
the task requires them to be copied. README.md has no `## Rule`/`## Verification`
sections, so the gate failed on it. Fix: extend the lint's existing skip list
(previously only `*.ask.md`) to also skip `README.md` and `TEMPLATE.md`. This is
consistent with the reference Merge instance, whose `always-on/` contains only
real guardrail specs and passes the gate. The existing `test_guardrail_lint.py`
still passes.
