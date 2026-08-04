"""Lint .flow/guardrails/ — each *.md (excluding *.ask.md) must have ## Rule
and ## Verification sections; IDs (**PREFIX-NN**) must be unique across files.

Usage:
    python -m flow_aidlc.checks.guardrail_lint                # uses .flow/guardrails/
    python -m flow_aidlc.checks.guardrail_lint <dir>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from flow_aidlc.checks._root import find_repo_root


_ID_RE = re.compile(r"\*\*([A-Z]+-\d+)\*\*")


def lint(guardrails_dir: Path | str) -> list[str]:
    """Return a list of error strings (empty → all clear)."""
    guardrails_dir = Path(guardrails_dir)
    errors: list[str] = []
    seen_ids: dict[str, Path] = {}  # id → first file that defined it

    for md_file in sorted(guardrails_dir.rglob("*.md")):
        # Skip *.ask.md — those are prompt-variant stubs, not guardrail specs.
        if md_file.name.endswith(".ask.md"):
            continue
        # Skip the always-on authoring aids shipped by the engine — README.md is
        # prose and TEMPLATE.md is a fill-in scaffold, not enforceable guardrails.
        if md_file.name in ("README.md", "TEMPLATE.md"):
            continue

        rel = str(md_file.relative_to(guardrails_dir))
        text = md_file.read_text(encoding="utf-8")

        # Section presence checks
        if "## Rule" not in text:
            errors.append(f"{rel}: missing '## Rule' section")
        if "## Verification" not in text:
            errors.append(f"{rel}: missing '## Verification' section")

        # ID uniqueness check
        for match in _ID_RE.finditer(text):
            gid = match.group(1)
            if gid in seen_ids:
                errors.append(
                    f"{rel}: duplicate ID {gid!r} (first seen in {seen_ids[gid].relative_to(guardrails_dir)})"
                )
            else:
                seen_ids[gid] = md_file

    return errors


def main(argv: list[str] | None = None) -> int:
    args = (argv or sys.argv)[1:]
    repo_root = find_repo_root()  # nearest ancestor containing .flow/
    guardrails_dir = Path(args[0]) if args else repo_root / ".flow" / "guardrails"

    errors = lint(guardrails_dir)
    if errors:
        print("guardrail-lint FAILED:")
        for e in errors:
            print(f"  {e}")
        return 1
    print("guardrail-lint OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
