# Publishing `flow-aidlc` to PyPI

The package name is **`flow-aidlc`**; it installs the **`flow`** CLI
(`[project.scripts] flow = "flow_aidlc.cli:main"`). The engine assets under
`src/flow_aidlc/engine/` ship as package data — `flow init` / `flow upgrade`
read them from the installed package, so they MUST be bundled in both the wheel
and the sdist (they are — see below).

> **Maintainer-only.** The steps below upload to a public index and require a
> PyPI API token. Run them yourself, with your own credentials — never commit a
> token, and never let an automated agent upload.

## 1. Pre-flight

```bash
# From the repo root, on a clean tree.
uv run --with pytest --with pyyaml python -m pytest -q   # all tests green
uv run python scripts/bump_version.py --check            # the three versions agree
```

The version lives in **three** files that must stay equal (the upgrade path
stamps `__version__` into each instance's `.flow/VERSION`, and the engine seed
must match): `pyproject.toml`, `src/flow_aidlc/__init__.py` (`__version__`), and
`src/flow_aidlc/engine/flow/VERSION`. Bump all three in lockstep with one command:

```bash
uv run python scripts/bump_version.py 0.1.1   # explicit version
# or: --patch / --minor / --major
```

It edits the three files, verifies they agree, and prints the remaining
build → check → upload → tag steps. It does **not** build, commit, or upload.
A `test_bump_version.py` guard fails CI if the three ever drift.

## 2. Build the distributions

```bash
python -m pip install --upgrade build twine   # one-time, in your build env
rm -rf dist/
python -m build                               # writes dist/*.whl and dist/*.tar.gz
```

`python -m build` produces both an sdist (`.tar.gz`) and a wheel
(`.whl`). Engine assets are included via:

- **wheel** — `[tool.setuptools.package-data]` in `pyproject.toml`
  (`engine/**/*` + `engine/**/.*` for any dot-prefixed files), and
- **sdist** — `MANIFEST.in` (`recursive-include src/flow_aidlc/engine *`).

## 3. Verify the artifacts before uploading

```bash
twine check dist/*        # metadata sanity — expect PASSED for both files

# Confirm the engine is actually bundled in the wheel:
python -c "import zipfile,glob; z=zipfile.ZipFile(glob.glob('dist/*.whl')[0]); \
print([n for n in z.namelist() if 'engine/flow/playbook.md' in n or 'engine/claude/commands' in n][:5])"
```

Optionally install the built wheel into a throwaway venv and smoke-test:

```bash
python -m venv /tmp/flow-smoke && /tmp/flow-smoke/bin/pip install dist/*.whl
/tmp/flow-smoke/bin/flow version
/tmp/flow-smoke/bin/flow init --yes --path /tmp/flow-smoke-repo && \
  /tmp/flow-smoke/bin/flow check /tmp/flow-smoke-repo
```

## 4. Upload

Test against TestPyPI first (recommended):

```bash
twine upload --repository testpypi dist/*
python -m pip install --index-url https://test.pypi.org/simple/ flow-aidlc
```

Then the real index:

```bash
twine upload dist/*
# Username: __token__
# Password: <your PyPI API token, starts with "pypi-">
```

Prefer a `~/.pypirc` or the `TWINE_USERNAME=__token__` / `TWINE_PASSWORD=<token>`
environment variables over typing the token interactively.

## 5. Post-release

- Tag the release: `git tag vX.Y.Z && git push --tags`.
- Verify the published install: `pip install --upgrade flow-aidlc && flow version`.
- Existing installs upgrade their engine assets with `flow upgrade` (instance
  files — config, guardrails, knowledge maps/decisions — are preserved).
