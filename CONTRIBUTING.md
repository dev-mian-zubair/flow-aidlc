# Contributing to flow-aidlc

Thanks for helping improve Flow — a governed, project-agnostic AI-DLC engine
shipped as a `flow` CLI + a Claude Code plugin. This guide covers local setup,
the change workflow, and the couple of repo-specific invariants to respect.

For the big picture (the engine-vs-instance boundary), read
[`ARCHITECTURE.md`](ARCHITECTURE.md) first.

## Development setup

Requirements: **Python ≥ 3.10** and [**uv**](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/dev-mian-zubair/flow-aidlc.git
cd flow-aidlc
uv run pre-commit install                       # enable the git hooks (once)
uv run --extra dev pytest -q                     # run the test suite (should be green)
```

`uv run` resolves dependencies on demand — there's no venv to activate.

## The everyday loop

```bash
uv run --extra dev pytest -q                      # tests
uv run pre-commit run --all-files                 # hooks (version-drift + hygiene)
uv run flow --help                                # exercise the CLI from source
```

- **Tests are required** for new behavior or bug fixes. Match the existing style
  in `tests/` (small, offline, one concern per test).
- Keep changes **focused** — one logical change per PR.

## Two repo-specific invariants

1. **Regenerate the plugin after editing engine Claude assets.** The engine's
   source of truth is `src/flow_aidlc/engine/claude/` (agents, commands, hooks).
   `plugin/` is a **generated** mirror — after changing any engine asset, run:

   ```bash
   uv run flow plugin build
   ```

   and commit the regenerated `plugin/` alongside your engine change. A drift
   between the two is a review blocker.

2. **Never hardcode project specifics in the engine.** Engine files ship
   **verbatim** at `flow init` (only `*.tmpl` files are token-rendered), so any
   literal is frozen into every install. Use the neutral placeholder
   `<TICKET-ID>` (never a real prefix), keep agents tracker- and language-neutral,
   and read project facts as data (`config.yaml`, guardrail files) rather than
   assuming them.

When editing agent instruction cards, follow the shared template already used
across `src/flow_aidlc/engine/claude/agents/**`: identity → **Load your guide**
→ **Inputs** → **Workflow** → **Return to caller** → **Least privilege**, with
`model: inherit`.

## Commit & PR conventions

- **Conventional-commit style** subject lines, matching the history:
  `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `ci:`, `build:`, `chore:`.
- Branch off `master`; open the PR against `master`.
- Before pushing: tests green, `pre-commit` clean, and (if you touched engine
  Claude assets) `plugin/` regenerated.
- Describe **what** changed and **why**; link any related issue.
- **Do not bump the version** in a feature/fix PR — releases are cut separately
  (see below), and version edits cause needless merge conflicts.

## Reporting bugs & requesting features

Open a GitHub issue with a minimal repro (the `flow` version from `flow version`,
your OS, and the exact command + output). Security-sensitive reports: please
avoid filing a public issue with exploit details — contact the maintainer first.

## Releases (maintainers only)

The version lives in three files kept in lockstep (`pyproject.toml`,
`src/flow_aidlc/__init__.py`, `src/flow_aidlc/engine/flow/VERSION`); the
`version-sync` pre-commit hook and CI guard block drift.

```bash
uv run python scripts/bump_version.py --patch     # or --minor / --major / X.Y.Z
uv run --extra dev pytest -q
git commit -am "release: v$(uv run python scripts/bump_version.py --show)"
git tag "v$(uv run python scripts/bump_version.py --show)"
git push && git push --tags                        # the tag triggers the release workflow
```

Pushing a `v*` tag runs `.github/workflows/release.yml`, which builds, tests,
and publishes to PyPI via Trusted Publishing (no token). Full details and the
one-time trusted-publisher setup: [`docs/PUBLISHING.md`](docs/PUBLISHING.md).

## License

By contributing, you agree that your contributions are licensed under the
project's [MIT License](LICENSE).
