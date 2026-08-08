"""`flow ci init` — scaffold a CI workflow that runs the Flow quality gate.

The gate (`flow check`) is designed to run in CI (dev == CI), but wiring it is
left to the user today. This command writes a ready-to-run workflow for the
chosen provider, parameterised from ``.flow/config.yaml`` (the base branch and
the configured ``graph.build``).

    flow ci init [--provider github|gitlab] [--path DIR] [--force] [--dry-run]

It never clobbers an existing workflow without ``--force``; ``--dry-run`` prints
the file it would write and touches nothing.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from flow_aidlc.checks._root import find_repo_root

try:
    import yaml
except ImportError:  # pragma: no cover - pyyaml is a runtime dependency
    yaml = None  # type: ignore[assignment]

_PROVIDERS = ("github", "gitlab")
_GATES = ("semgrep", "conftest")

# Extra deterministic gate steps that run alongside `flow check` (opt-in via --gates).
# Guardrails are LLM-judged; these are deterministic SAST / policy-as-code checks.
_GH_GATE_STEPS = {
    "semgrep": (
        "      - name: Semgrep SAST\n"
        "        run: pipx install semgrep && semgrep scan --config auto --error --quiet\n"
    ),
    "conftest": (
        "      - name: Policy check (conftest)\n"
        '        run: docker run --rm -v "$PWD:/project" -w /project openpolicyagent/conftest test .flow/config.yaml .mcp.json -p policy\n'
    ),
}
_GL_GATE_STEPS = {
    "semgrep": "    - pip install semgrep && semgrep scan --config auto --error --quiet\n",
    "conftest": '    - docker run --rm -v "$PWD:/project" -w /project openpolicyagent/conftest test .flow/config.yaml .mcp.json -p policy\n',
}


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="flow ci", description="Scaffold CI that runs `flow check`.")
    sub = p.add_subparsers(dest="action", required=True)
    init = sub.add_parser("init", help="Write a CI workflow that runs the quality gate.")
    init.add_argument("--provider", choices=_PROVIDERS, default="github")
    init.add_argument("--path", default=None, help="Repo dir (default: search up from cwd).")
    init.add_argument("--force", action="store_true", help="Overwrite an existing workflow.")
    init.add_argument("--dry-run", action="store_true", help="Print the workflow; write nothing.")
    init.add_argument("--gates", default="", help="Extra deterministic gates, comma-separated: semgrep, conftest.")
    return p


def run(argv: list[str]) -> int:
    try:
        args = _parser().parse_args(argv)
    except SystemExit:
        return 2
    root = find_repo_root(args.path)
    if args.action == "init":
        gates = [g.strip() for g in args.gates.split(",") if g.strip()]
        unknown = [g for g in gates if g not in _GATES]
        if unknown:
            sys.stderr.write(f"flow ci: unknown gate(s): {', '.join(unknown)}. Supported: {', '.join(_GATES)}\n")
            return 2
        return _init(root, args.provider, args.force, args.dry_run, gates)
    return 2


def _config(root: Path) -> tuple[str, str]:
    """Return (base_branch, graph_build) from .flow/config.yaml, with defaults.

    ``vcs.base`` may be a tracking ref like ``origin/main``; CI triggers want the
    bare branch name, so the leading remote is stripped.
    """
    base, build = "main", ""
    cfg = root / ".flow" / "config.yaml"
    if yaml is not None and cfg.exists():
        try:
            data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            data = {}
        base = str((data.get("vcs") or {}).get("base") or base)
        build = str((data.get("graph") or {}).get("build") or "")
    return base.rsplit("/", 1)[-1], build


def _github_workflow(base: str, build: str, gates: list[str]) -> str:
    graph_step = f"      - name: Build code graph\n        run: {build}\n" if build else ""
    gate_steps = "".join(_GH_GATE_STEPS[g] for g in gates)
    return (
        "name: flow check\n\n"
        "on:\n"
        f"  pull_request:\n    branches: [{base}]\n"
        f"  push:\n    branches: [{base}]\n\n"
        "jobs:\n"
        "  flow-check:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - uses: actions/setup-python@v5\n"
        '        with:\n          python-version: "3.12"\n'
        "      - name: Install Flow + graph tool\n"
        "        run: pipx install flow-aidlc && pipx install graphifyy\n"
        f"{graph_step}"
        "      - name: Run the quality gate\n"
        "        run: flow check\n"
        f"{gate_steps}"
    )


def _gitlab_ci(base: str, build: str, gates: list[str]) -> str:
    build_line = f"    - {build}\n" if build else ""
    gate_steps = "".join(_GL_GATE_STEPS[g] for g in gates)
    return (
        "# Flow quality gate — runs `flow check` on merge requests.\n"
        "flow-check:\n"
        "  image: python:3.12\n"
        "  rules:\n"
        '    - if: $CI_PIPELINE_SOURCE == "merge_request_event"\n'
        "  script:\n"
        "    - pip install flow-aidlc graphifyy\n"
        f"{build_line}"
        "    - flow check\n"
        f"{gate_steps}"
    )


def _init(root: Path, provider: str, force: bool, dry: bool, gates: list[str]) -> int:
    base, build = _config(root)
    if provider == "github":
        dest = root / ".github" / "workflows" / "flow-check.yml"
        content = _github_workflow(base, build, gates)
    else:
        dest = root / ".gitlab-ci.yml"
        content = _gitlab_ci(base, build, gates)

    rel = dest.relative_to(root)
    if dest.exists() and not force:
        print(f"{rel} already exists — use --force to overwrite.")
        return 1
    if dry:
        print(f"DRY-RUN: would write {rel}:\n")
        print(content)
        return 0

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    print(f"Wrote {rel} — runs `flow check` on {provider} (base branch: {base}).")
    print("If flow-aidlc isn't on PyPI yet, adjust the install step to your source.")
    return 0
