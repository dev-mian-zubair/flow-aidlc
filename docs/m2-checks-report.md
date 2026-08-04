# M2 — Vendored Flow quality-gate checks + CLI wiring

Status: DONE

## 1. Check modules vendored

Copied from `scripts/flow-checks/flow_checks/` (reference instance) into
`src/flow_aidlc/checks/`, logic unchanged except imports and root discovery:

- `guardrail_lint.py`
- `structure_check.py`
- `freshness.py`
- `scorer.py`
- `reference_check.py`
- `traceability.py`
- `learnings.py`
- `artifact_sensor.py`
- `gate.py`

`checks/__init__.py` was already present and left in place. New helper added:
`checks/_root.py` (`find_repo_root()`).

## 2. Import rewrites

- All internal imports rewritten `flow_checks.X` → `flow_aidlc.checks.X`.
  Only cross-module imports were `gate.py` (imports the four check modules) and
  `reference_check.py` (imports `scorer.score_dirs`). Both updated.
- Docstring / usage-string module references (`python -m flow_checks.X`) also
  updated to `flow_aidlc.checks.X` so the module paths are correct.
- Engine asset docs under `src/flow_aidlc/engine/**` that referenced
  `python -m flow_checks.*` as example commands were updated to
  `flow_aidlc.checks.*` (6 markdown files: build-verify.md, checkpoint-reviewer.md,
  traceability.md, slicing.md, design.md, learnings.md) so the grep contract
  (`grep -rn flow_checks src/flow_aidlc tests` → nothing) holds.

## 3. Repo-root generalization

`Path(__file__).resolve().parents[3]` (correct only in the old
`scripts/flow-checks/flow_checks/` layout) replaced with `find_repo_root()` in
the `main()` default path of:

- `gate.py`
- `structure_check.py`
- `freshness.py`
- `guardrail_lint.py` (also carried a `parents[3]` default in `main()` and a
  now-wrong comment; generalized for correctness — logic unaffected since
  `gate.run` always passes explicit dirs)

`find_repo_root(start)` walks up from `start` (default cwd) to the first
ancestor containing `.flow/`, falling back to `start`. Explicit-arg paths in
each `check()`/`run()` and `main()` positional are preserved — callers can still
pass a root/flow_dir.

## 4. Tests vendored

Copied `tests/test_*.py` → `tests/`, imports rewritten to `flow_aidlc.checks.X`.
`tests/__init__.py` copied (empty). Fixture `reference-runs/add-readonly-endpoint`
(baseline.yaml + golden/shape/{requirements,design,slices}.md) vendored to
`reference-runs/` at package root — `test_reference_check.py` and one
`test_scorer.py` test locate it via `Path(__file__).resolve().parents[1]`, which
in the new `tests/` layout resolves to the package root, so the bundled fixture
is found with no dependency on the PIP repo.

`pyproject.toml` gained:

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

### Test result

58 passed, 0 skipped, 0 failed (run under a python with pytest + pyyaml).
No tests had to be skipped or made repo-dependent — the two fixture-backed
tests use the vendored `reference-runs/` bundle.

## 5. CLI wiring (stubs replaced)

- `commands/check.py` — parses optional `[path]` (default cwd) + `--strict`;
  `root = find_repo_root(path)`; if no `.flow/` → prints
  "flow check: no .flow/ here — run `flow init` first." and returns 2; else
  `gate.run(root, strict_freshness=...)` and returns its exit code.
- `commands/refresh.py` — `root = find_repo_root()`; runs `freshness.check(root)`;
  prints stale docs (or "all knowledge maps are fresh"); notes that re-derivation
  is done by the `curator` subagent via `/flow-refresh` in Claude Code.
  Report-only (exit 0) unless `--strict` and stale → 1. (Also returns 2 with the
  init hint if no `.flow/`.)
- `commands/selftest.py` — locates the vendored `tests/` dir relative to the
  package (the `tests/` sibling of `src/`), then
  `subprocess.run([sys.executable, "-m", "pytest", "-q", <tests_dir>, *argv])`,
  list form, no shell. If pytest is unimportable, prints
  `pip install flow-aidlc[dev]` and returns 2; otherwise returns pytest's exit
  code.

## 6. Validation performed

- `PYTHONPATH=src python3 -c "from flow_aidlc.checks import ...; find_repo_root"` → imports OK.
- `PYTHONPATH=src pytest tests/ -q` → 58 passed.
- `flow check` from a dir with no `.flow/` → prints the init hint, exit 2, no traceback.
- `flow check` in a scaffolded `.flow/` → runs all 4 checks, "gate PASSED", exit 0.
- `flow refresh` (no knowledge-map) → "all knowledge maps are fresh", exit 0.
- `flow selftest` (with pytest available) → runs the 58 vendored tests.
- `grep -rn "flow_checks" src/flow_aidlc tests` → nothing.

## Notes

- pytest is not in the system `python3` on this machine; the vendored tests and
  `flow selftest` were verified using a python that has pytest+pyyaml. End users
  get this via `pip install flow-aidlc[dev]` (the `dev` extra already pins
  `pytest>=7`).
