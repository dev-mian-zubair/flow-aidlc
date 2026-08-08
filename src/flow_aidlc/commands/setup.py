"""`flow setup` — portable one-command onboarding for a Flow repo.

The package replacement for a project's ``make flow-setup`` target. It chains the
*automatable* onboarding steps against the target repo, in order:

1. **Graph tool** — if ``uv`` is on PATH, install the pinned Graphify build
   (``uv tool install "graphifyy[mcp]==0.9.33" --force``); otherwise print the
   install hint and continue. (detect + guide + keep going)
2. **Build the graph** — run the configured ``graph.build`` command from
   ``config.yaml`` when its binary is on PATH; otherwise guide and continue.
3. **Doctor** — run ``flow doctor`` for the readiness check.

It is deliberately forgiving: a missing external tool is a WARN + a hint, never a
hard failure — so ``flow setup`` always finishes the steps it *can* do. The two
steps only a human can finish (a tracker token, reloading MCP servers in the
client) are surfaced by ``flow doctor`` at the end.

Usage:
    flow setup [--path DIR] [--dry-run]
"""
from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from flow_aidlc.checks._root import find_repo_root

try:
    import yaml
except ImportError:  # pragma: no cover - pyyaml is a runtime dependency
    yaml = None  # type: ignore[assignment]

# The pinned Graphify build the code-graph adapter targets (see steps/shared/graph.md).
_GRAPHIFY_SPEC = "graphifyy[mcp]==0.9.33"

_IMPECCABLE_EPHEMERA = (
    ".impeccable/*.png", ".impeccable/sessions/", ".impeccable/previews/",
    ".impeccable/cache/", ".impeccable/config.local.json",
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="flow setup",
        description="Portable one-command onboarding: graph tool + graph build + doctor.",
    )
    p.add_argument("--path", default=None, help="Directory to search upward from for a .flow/ (default: cwd).")
    p.add_argument("--dry-run", action="store_true", help="Print the planned chain; run nothing external.")
    p.add_argument("--with-impeccable", action="store_true",
                   help="Also install the Impeccable design-quality skill (opt-in; UI projects).")
    return p


def _graph_build_cmd(flow_dir: Path) -> str:
    """Return the configured ``graph.build`` command, or '' if absent/unreadable."""
    config_path = flow_dir / "config.yaml"
    if yaml is None or not config_path.exists():
        return ""
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return ""
    graph = data.get("graph", {}) or {}
    return str(graph.get("build") or "")


def _run(cmd: list[str], cwd: Path) -> int:
    """Run ``cmd`` in ``cwd``, streaming output; return its exit code (or 127 if absent)."""
    try:
        return subprocess.run(cmd, cwd=str(cwd)).returncode
    except FileNotFoundError:
        return 127


def _ensure_impeccable_gitignore(root: Path) -> None:
    """Append Impeccable ephemera to .gitignore (PRODUCT.md/DESIGN.md stay tracked)."""
    path = root / ".gitignore"
    existing = set()
    text = ""
    if path.exists():
        text = path.read_text(encoding="utf-8")
        existing = {ln.strip() for ln in text.splitlines()}
    missing = [e for e in _IMPECCABLE_EPHEMERA if e not in existing]
    if not missing:
        return
    prefix = "" if (not text or text.endswith("\n")) else "\n"
    path.write_text(text + prefix + "\n".join(missing) + "\n", encoding="utf-8")


def run(argv: list[str]) -> int:
    args = _build_parser().parse_args(argv)
    dry = args.dry_run

    root = find_repo_root(args.path)
    flow_dir = root / ".flow"
    if not flow_dir.exists():
        sys.stderr.write(
            f"flow setup: no .flow/ found at or above {root} — run `flow init` first.\n"
        )
        return 1

    def step(msg: str) -> None:
        print(("DRY-RUN: would " if dry else "") + msg)

    print(f"Flow setup — target: {root}\n")

    # ---- 1. graph tool (detect uv; guide if absent) -----------------------
    if shutil.which("uv"):
        step(f"install the graph tool: uv tool install \"{_GRAPHIFY_SPEC}\" --force")
        if not dry:
            rc = _run(["uv", "tool", "install", _GRAPHIFY_SPEC, "--force"], root)
            if rc != 0:
                print(f"  [WARN] graph-tool install exited {rc} — continuing.")
    else:
        print("  [WARN] `uv` not found — skipping graph-tool install.")
        print(f"         Install uv, then: uv tool install \"{_GRAPHIFY_SPEC}\" --force")

    # ---- 2. build the graph (if the build binary is on PATH) --------------
    build_cmd = _graph_build_cmd(flow_dir)
    if build_cmd:
        binary = shlex.split(build_cmd)[0] if build_cmd.strip() else ""
        if binary and shutil.which(binary):
            step(f"build the code graph: {build_cmd}")
            if not dry:
                rc = _run(shlex.split(build_cmd), root)
                if rc != 0:
                    print(f"  [WARN] graph build exited {rc} — continuing.")
        else:
            print(f"  [WARN] graph.build binary '{binary}' not on PATH — skipping graph build.")
            print(f"         Once installed, run: {build_cmd}")
    else:
        print("  [WARN] no graph.build in config.yaml — skipping graph build.")

    # ---- 3. doctor --------------------------------------------------------
    step("run the readiness check: flow doctor")
    if not dry:
        from flow_aidlc.commands import doctor

        # Doctor never hard-fails setup; its verdict is advisory here.
        try:
            doctor.run(["--path", str(root)])
        except SystemExit:  # pragma: no cover - defensive
            pass

    # ---- 4. Impeccable (opt-in) ------------------------------------------
    if args.with_impeccable:
        step("install Impeccable (design quality): npx impeccable install --providers=claude --scope=project")
        if not dry:
            if shutil.which("npx"):
                rc = _run(["npx", "--yes", "impeccable", "install", "--providers=claude", "--scope=project"], root)
                if rc != 0:
                    print(f"  [WARN] impeccable install exited {rc} — continuing.")
            else:
                print("  [WARN] `npx` not found — skipping Impeccable install.")
                print("         Install Node, then: npx impeccable install --providers=claude --scope=project")
            _ensure_impeccable_gitignore(root)
        print("  Author the standards in Claude Code: run `/impeccable init` to create PRODUCT.md + DESIGN.md")
        print("  (they are committed; Flow reads them for grounding — see INTEGRATIONS.md)")

    print("\nFlow setup complete." + (" (dry-run — nothing external ran.)" if dry else ""))
    print("Finish the human-only steps flagged by `flow doctor` above")
    print("  (e.g. a tracker token, then reload MCP servers in your client).")
    return 0
