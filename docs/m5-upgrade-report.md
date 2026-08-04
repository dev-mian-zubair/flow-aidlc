# M5 — `flow upgrade` + PyPI build-readiness

## Scope delivered

1. `flow upgrade [--path DIR] [--dry-run] [--force]` — refreshes engine assets in
   an installed repo without touching the user's instance material.
2. Shared `merge_settings` helper factored out of `init` so upgrade re-merges
   hooks with identical logic.
3. Packaging: `MANIFEST.in` for the sdist; confirmed `pyproject.toml`
   package-data covers the wheel; build + inspect + `twine check`.
4. `docs/PUBLISHING.md` — maintainer publish runbook.

## Upgrade logic (`src/flow_aidlc/commands/upgrade.py`)

- **Discovery / guards.** `find_repo_root(--path or cwd)`; no `.flow/` →
  `"not a Flow repo — run flow init first"`, return 2. Reads the engine
  `manifest.yaml`, the target `.flow/VERSION`, and the package `__version__`.
  Equal + not `--force` → `"already up to date (vX)"`, return 0.
- **Tree walk.** Iterates every file under the packaged `engine/`. Each engine
  file maps to its target: `flow/*`→`.flow/*`, `claude/*`→`.claude/*`,
  `knowledge/*`→`knowledge/*`. Engine-root files that map to no tree
  (`README.md`, `manifest.yaml`) are skipped — `flow init` never copies them
  into a repo, so upgrade leaves them alone.
- **Manifest classification.** A path is `engine` unless it matches an
  `instance` glob; when both match, the **longer (more specific) glob wins**
  (ties → engine). This makes `always-on/README.md` and `always-on/TEMPLATE.md`
  engine even though `always-on/**` is an instance dir, and likewise
  `knowledge/map/README.md` / `decisions/README.md` engine inside instance dirs.
  Glob matching (`_matches`) uses `fnmatch` plus an explicit `/**` rule so a
  trailing `/**` also matches the directory prefix itself. Verified against the
  real manifest — see the sanity table run during development (all 15 cases
  classified as expected).
- **Actions per file:**
  - **engine** → copy the packaged file over the target (create if missing);
    hooks (`.sh` under `hooks/`) re-chmod +x.
  - **instance** → SKIP (never overwrite guardrails / knowledge maps / decisions
    / practices / rendered configs).
  - **`*.tmpl.*`** → SKIP unconditionally (the rendered instance files —
    `config.yaml`, `knowledge-map.yaml`, `.mcp.json` — are the user's).
  - **`claude/settings.json`** → RE-MERGE via the shared `merge_settings`
    (append engine hook entries, dedupe identical commands, preserve the user's
    other keys) rather than blind copy.
- **`--dry-run`** prints every planned action (`UPDATE` / `MERGE` /
  `skip-inst` / `skip-tmpl`) and writes nothing (VERSION untouched too).
- After a real run, writes the package `__version__` to `.flow/VERSION` and
  prints an `N updated / M preserved / old→new` summary.

### Design note: `.tmpl.` skip breadth

The spec says "skip all `*.tmpl.*` files". `_is_tmpl` matches any `.tmpl.` in the
name, so besides the three config templates it also skips the artifact templates
under `flow/templates/*.tmpl.md`. This is deliberate and safe: `flow guardrail
add` mutates `.flow/templates/requirements.tmpl.md` (regenerating the guardrail
checklist), so those files carry user content post-init; overwriting them on
upgrade would clobber it. The trade-off is that engine-side improvements to
artifact templates do not auto-propagate — acceptable, and matches the literal
instruction. (The manifest still classifies `flow/templates/**` as engine; the
`.tmpl.` skip is a stronger, earlier guard.)

## Shared settings-merge

`_merge_settings` moved from `init.py` into `engine_assets.merge_settings`
(public). `init.py` now imports and calls it; its now-unused `json` import was
removed. This is the single source of truth for hook-merge semantics used by both
`init` (first scaffold) and `upgrade` (re-merge). All existing init tests still
pass, confirming behavior is unchanged.

## Tests (`tests/test_upgrade.py`)

- `test_upgrade_replaces_engine_preserves_instance` — init; rewind
  `.flow/VERSION` to `0.0.1`; corrupt `.flow/playbook.md` to `"STALE"`; author an
  instance guardrail (`guardrail add my-inv --prefix MY`) and record its bytes;
  add `# USER EDIT` to `config.yaml`; run `upgrade`. Asserts: playbook restored
  and byte-equal to the packaged engine playbook; the authored guardrail is
  byte-identical; `config.yaml` still has `# USER EDIT` and `my-inv`;
  `.flow/VERSION` == package version; `gate.run(tmp) == 0`.
- `test_upgrade_noop_when_current` — init then `upgrade` → up-to-date, rc 0,
  playbook bytes unchanged, VERSION == package version.
- `test_upgrade_dry_run_writes_nothing` — rewind VERSION + corrupt playbook;
  `upgrade --dry-run` → rc 0; playbook still `"STALE"`; VERSION still `0.0.1`.
- `test_upgrade_not_a_flow_repo` — outside a Flow repo → rc 2.

**Result:** `74 passed` (70 pre-existing + 4 new).

End-to-end smoke (outside pytest): init a temp repo, rewind VERSION, corrupt
`playbook.md`, author a guardrail, `flow upgrade` → playbook restored, guardrail
byte-preserved, VERSION `0.0.1 → 0.1.0`, `flow check <repo>` → `gate PASSED`.

## Packaging / build

- **`MANIFEST.in`** added: `recursive-include src/flow_aidlc/engine *` (plus a
  `.*` line for dot-prefixed engine files), and README/LICENSE/ARCHITECTURE.
- **`pyproject.toml`** already ships `engine/**/*` **and** `engine/**/.*` under
  `[tool.setuptools.package-data]` — dot-prefixed engine files are covered. No
  change needed; verified correct.
- **Build.** The provided test venv has no pip/`build`; `python -m build`
  succeeded using a pypa-`build` 1.5.0 install (via an available toolchain, with
  network for build isolation). Both distributions built:
  `flow_aidlc-0.1.0-py3-none-any.whl` and `flow_aidlc-0.1.0.tar.gz`.
- **Bundling verified.**
  - Wheel: **82** `flow_aidlc/engine/**` entries, including
    `engine/flow/playbook.md`, `engine/manifest.yaml`,
    `engine/claude/settings.json`, `engine/claude/commands/*`.
  - Sdist: contains `engine/flow/playbook.md` and `MANIFEST.in`; **105**
    engine-path entries.
  - `twine check dist/*` → **PASSED** for both files.

**Conclusion: the built artifacts DO bundle the engine assets** (wheel and sdist).
`dist/` is gitignored and left in place for inspection; nothing was uploaded.

## Docs

`docs/PUBLISHING.md` — the exact publish sequence (`python -m build`,
`twine check dist/*`, `twine upload dist/*` with a PyPI `__token__`), the
three-place version bump, artifact-verification commands, and a clear
maintainer-runs-with-own-credentials caveat. Package name `flow-aidlc`, CLI
`flow`.
