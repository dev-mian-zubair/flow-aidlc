# M4 Authoring-Helper Commands — Implementation Report

Implements the three M4 authoring helpers on top of a repo already scaffolded by
`flow init`: `flow guardrail add`, `flow map add`, and `flow doctor`. Each was a
stub returning `staged(...)`; now fully implemented, matching the existing
command style (`init.py`, `check.py`, `version.py`).

## Files written

- `src/flow_aidlc/commands/guardrail.py` — `flow guardrail add <name> [--prefix PREFIX] [--optional] [--path DIR]`
- `src/flow_aidlc/commands/map.py` — `flow map add <glob> <doc> [--title T] [--path DIR]`
- `src/flow_aidlc/commands/doctor.py` — `flow doctor [--path DIR]`
- `tests/test_authoring.py` — 9 tests using real init-scaffolded tmp repos

No other files changed. No git commit; no worktree.

## Design notes

### `--path` flag (testability)
All three commands accept an optional `--path DIR` (default: cwd). The repo root
is resolved via `find_repo_root(args.path)`, so tests can point at a tmp repo
without `os.chdir`. This mirrors `init.py`'s `--path`. When no `.flow/` is found,
each command prints `not a Flow repo — run \`flow init\` first` and returns 2.

### guardrail add
- `<name>` validated as kebab-case; else error + return 2.
- Prefix default derived from the **first** hyphen-part, leading letters, up to 3
  chars (`budget-integrity`→`BUD`, `license-sku-gating`→`LIC`). The spec's two
  worked examples both take from the first word only (not one initial per part),
  so first-word derivation is what reproduces them. `--prefix` overrides.
- Scaffolds from `guardrails/always-on/TEMPLATE.md`, substituting the title, the
  ID-prefix hint line, and the example rule ids (`**[PREFIX]-01**` → `**BUD-01**`).
  The rendered file keeps `## Rule` + `## Verification`, so it passes
  `guardrail_lint`.
- `--optional` places the file under `optional/` and registers under
  `guardrails.optional`; otherwise `always-on/` + `guardrails.always_on`.
- Refuses if the target `.md` already exists (return 1).
- **Config registration is a targeted, comment-preserving line edit:** only the
  inline list value on the `always_on:` / `optional:` line is parsed with yaml,
  appended (no dupes), and re-serialized as an inline flow list `[a, b]`. The
  rest of the file — including all comments — is left byte-for-byte intact. (A
  full pyyaml round-trip was deliberately avoided; it strips comments.)
- **Requirements checklist regeneration** (always-on only): rewrites the
  `## Guardrail impact checklist` table body to one row per `always_on`
  guardrail, reading the list back from config after the edit. Keeps the table
  header + separator; empty list → a single `<!-- no always-on guardrails yet -->`
  placeholder row. Optional guardrails do not appear in the checklist.

### map add
- Creates `knowledge/map/<doc>.md` with `status: FRESH` / `derives-from: [<glob>]`
  / `verified-at-sha: <short HEAD>` frontmatter, a `# <Title|doc>` heading, and a
  one-line-description placeholder.
- Short HEAD via `subprocess.run(["git","rev-parse","--short","HEAD"], ...)`
  (list form). Not a git repo / no commits → `UNKNOWN` + a stderr warning.
- Refuses if the doc already exists (return 1).
- Registers under `maps:` in `.flow/knowledge-map.yaml`, preserving existing
  entries and comments. Handles both the `maps: []` seed (upgraded to a block
  list) and an existing block list (appended at the block's end). Output stays
  valid YAML (verified by re-loading in tests).

### doctor
Read-only. Prints a `[PASS]/[WARN]/[FAIL]` line per check, an overall verdict,
then `Run \`flow check\` for the full quality gate.` Returns 0 if no FAIL, else 1.
Checks: Flow present · config valid (reuses `structure_check`) · guardrails
(WARN if always_on empty) · hooks (expected `*.sh` present + executable +
referenced-by-settings.json resolve) · knowledge (map yaml parses, docs exist,
freshness → WARN if stale) · git (WARN if absent) · mcp (WARN if absent; lists
non-`_` server names).

## Validation

- **Test suite:** `PYTHONPATH=src <venv-python> -m pytest tests/ -q` → **70 passed**
  (61 pre-existing + 9 new in `test_authoring.py`).
- **End-to-end:** fresh `git init` + `flow init`, then
  `flow guardrail add my-invariant`, `flow map add "src/**" my-map`,
  `flow doctor`, `flow check`:
  - `flow doctor` → all seven checks `[PASS]`, Verdict OK, **exit 0**.
  - `flow check` → **gate PASSED, exit 0**.
  - Config + knowledge-map comments confirmed preserved after edits;
    `maps: []` seed correctly upgraded to a block list.

### doctor output (fresh e2e repo)

```
[PASS] Flow present — .flow/ + playbook.md + config.yaml
[PASS] config valid — config parses; guardrail names resolve to files
[PASS] guardrails — 1 always-on, 3 optional
[PASS] hooks — 7 hooks present, executable, wired in settings.json
[PASS] knowledge — 1 maps, all docs present and fresh
[PASS] git — .git present
[PASS] mcp — servers: context7, github

Verdict: OK
Run `flow check` for the full quality gate.
```
