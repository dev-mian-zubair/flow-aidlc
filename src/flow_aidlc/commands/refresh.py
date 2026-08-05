"""`flow refresh` — structure-freshness is now graph-based.

The doc-freshness loop (comparing each knowledge map's ``verified-at-sha``
against git history) has been RETIRED per ADR 0008/0009. Code *structure* now
lives in a committed code graph (Graphify), which is fresh-by-construction — you
rebuild it with the configured ``graph.build`` command. Curated ``knowledge/map/``
docs hold only *invariants*; verifying those against the code graph is the
`curator` subagent's job, dispatched via ``/flow-refresh`` inside Claude Code.

So this command:
  * rebuilds the code graph by running ``config.yaml → graph.build`` (offering to
    run it if the backend binary is on PATH; otherwise printing an install hint), and
  * points you at ``/flow-refresh`` for invariant curation.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

from flow_aidlc.checks._root import find_repo_root

try:
    import yaml  # pyyaml
except ImportError:  # pragma: no cover - pyyaml is a runtime dependency
    yaml = None  # type: ignore[assignment]


def _graph_build_command(root) -> str | None:
    """Read ``config.yaml → graph.build``; return the command string or None."""
    cfg_path = root / ".flow" / "config.yaml"
    if yaml is None or not cfg_path.exists():
        return None
    try:
        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return None
    build = (data.get("graph", {}) or {}).get("build")
    return str(build) if build else None


def run(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="flow refresh",
        description="Rebuild the code graph (structure freshness) and point at /flow-refresh for invariant curation.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the graph-build command without executing it.",
    )
    parsed = parser.parse_args(argv)

    root = find_repo_root()
    if not (root / ".flow").is_dir():
        sys.stderr.write(
            "flow refresh: no .flow/ here — run `flow init` first.\n"
        )
        return 2

    print(
        "Structure freshness is now graph-based (ADR 0008/0009): the doc-freshness\n"
        "loop is retired. Code structure lives in a committed code graph — rebuild it\n"
        "with the configured `graph.build` command; use `/flow-refresh` in Claude Code\n"
        "for invariant curation (the curator verifies map invariants against the graph)."
    )
    print()

    build_cmd = _graph_build_command(root)
    if not build_cmd:
        print(
            "No `graph.build` command configured in .flow/config.yaml (graph.build) — "
            "nothing to rebuild. Add a `graph:` block or run `/flow-refresh` for invariant curation."
        )
        return 0

    argv_list = build_cmd.split()
    binary = argv_list[0] if argv_list else ""

    if parsed.dry_run:
        print(f"[dry-run] would run: {build_cmd}")
        return 0

    if binary and shutil.which(binary):
        print(f"Running graph build: {build_cmd}")
        try:
            subprocess.run(argv_list, cwd=root, check=True)
        except subprocess.CalledProcessError as exc:
            sys.stderr.write(f"flow refresh: graph build failed (exit {exc.returncode}).\n")
            return 0  # report-only: never hard-fail the caller
        print("Graph rebuilt. Now run `/flow-refresh` in Claude Code for invariant curation.")
    else:
        print(
            f"Graph backend binary '{binary}' is not on PATH — cannot rebuild here.\n"
            f"Install it (e.g. `uv tool install \"graphifyy[mcp]\"`), then run:  {build_cmd}"
        )

    return 0
