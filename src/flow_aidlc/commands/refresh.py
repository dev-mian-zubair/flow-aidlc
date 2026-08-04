"""`flow refresh` — report knowledge maps that have drifted out of date.

This is the report-only half of the freshness loop: it compares each knowledge
doc's ``verified-at-sha`` against git history and lists the stale ones. It does
NOT re-derive them — that is the `curator` subagent's job, dispatched via
`/flow-refresh` inside Claude Code. Report-only means exit 0 even when docs are
stale, unless ``--strict`` is passed.
"""
from __future__ import annotations

import argparse
import sys

from flow_aidlc.checks import freshness
from flow_aidlc.checks._root import find_repo_root


def run(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="flow refresh",
        description="Report knowledge maps that are stale relative to the code they derive from.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any knowledge map is stale (default: report-only, exit 0).",
    )
    parsed = parser.parse_args(argv)

    root = find_repo_root()
    if not (root / ".flow").is_dir():
        sys.stderr.write(
            "flow refresh: no .flow/ here — run `flow init` first.\n"
        )
        return 2

    stale = freshness.check(root)

    if stale:
        print("Stale knowledge maps (code changed since verified-at-sha):")
        for doc in stale:
            print(f"  STALE: {doc}")
        print()
        print(
            "Re-derivation is done by the `curator` subagent via `/flow-refresh` "
            "in Claude Code — this command only reports."
        )
        return 1 if parsed.strict else 0

    print("all knowledge maps are fresh")
    return 0
