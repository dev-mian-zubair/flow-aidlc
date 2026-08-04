"""`flow check` — run the composed quality gate against a Flow instance.

Resolves the repo root by walking up to the nearest `.flow/`, then hands off to
``flow_aidlc.checks.gate.run``. If there is no `.flow/` anywhere above the given
path, we bail with a helpful message rather than running the gate against a
directory that was never initialised.
"""
from __future__ import annotations

import argparse
import sys

from flow_aidlc.checks import gate
from flow_aidlc.checks._root import find_repo_root


def run(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="flow check",
        description="Run the Flow quality gate (guardrail-lint, structure, freshness, reference-selfcheck).",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Directory to search upward from for a .flow/ (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat freshness drift as blocking (default: warn-only).",
    )
    parsed = parser.parse_args(argv)

    root = find_repo_root(parsed.path)
    if not (root / ".flow").is_dir():
        sys.stderr.write(
            "flow check: no .flow/ here — run `flow init` first.\n"
        )
        return 2

    return int(gate.run(root, strict_freshness=parsed.strict))
