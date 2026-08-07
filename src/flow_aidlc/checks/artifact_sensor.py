"""Deterministic artifact sensors for Flow stage markdown files.

Checks that a stage artifact has its required sections and cites its upstream
inputs — offline, no LLM, no network. A deterministic artifact "sensor".

Usage:
    python -m flow_aidlc.checks.artifact_sensor <file> \\
        --require "## Rule,## Verification" \\
        --upstream "requirements.md,design.md"

Exits 0 if clean, 1 if any findings.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def required_sections(text: str, required: list[str]) -> list[str]:
    """Return the required headings NOT present in *text*.

    A heading is considered present if any line in *text* equals it exactly
    OR starts with it (e.g. ``## Rule: details`` satisfies ``## Rule``).

    Returns an empty list when all required headings are present.
    """
    if not required:
        return []

    lines = text.splitlines()
    missing: list[str] = []
    for heading in required:
        found = any(line == heading or line.startswith(heading) for line in lines)
        if not found:
            missing.append(heading)
    return missing


def upstream_coverage(text: str, upstream: list[str]) -> list[str]:
    """Return the upstream names NOT cited anywhere in *text*.

    The search is a plain case-insensitive substring match.

    Returns an empty list when all upstream names are cited.
    """
    if not upstream:
        return []

    text_lower = text.lower()
    return [name for name in upstream if name.lower() not in text_lower]


def sense(
    path: Path | str,
    required: list[str] | None = None,
    upstream: list[str] | None = None,
) -> list[str]:
    """Read the file at *path* and return a combined list of finding strings.

    Findings are prefixed:
    - ``"missing section: ## Heading"``
    - ``"missing upstream citation: name.md"``
    - ``"file not found: <path>"``

    Returns ``[]`` if the file is clean.  A missing file returns a single
    ``"file not found"`` finding and never raises.
    """
    path = Path(path)
    if not path.exists():
        return [f"file not found: {path}"]

    text = path.read_text(encoding="utf-8", errors="replace")
    findings: list[str] = []

    for heading in required_sections(text, required or []):
        findings.append(f"missing section: {heading}")

    for name in upstream_coverage(text, upstream or []):
        findings.append(f"missing upstream citation: {name}")

    return findings


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    python -m flow_aidlc.checks.artifact_sensor <file>
        --require "## Rule,## Verification"
        --upstream "requirements.md,design.md"
    """
    parser = argparse.ArgumentParser(
        description="Deterministic artifact sensor for Flow stage markdown files.",
    )
    parser.add_argument("file", help="Path to the artifact markdown file.")
    parser.add_argument(
        "--require",
        default="",
        metavar="HEADINGS",
        help="Comma-separated list of required section headings (e.g. '## Rule,## Verification').",
    )
    parser.add_argument(
        "--upstream",
        default="",
        metavar="NAMES",
        help="Comma-separated list of upstream file names that must be cited.",
    )

    parsed = parser.parse_args(argv if argv is not None else sys.argv[1:])

    required = [h.strip() for h in parsed.require.split(",") if h.strip()] if parsed.require else []
    upstream = [u.strip() for u in parsed.upstream.split(",") if u.strip()] if parsed.upstream else []

    findings = sense(parsed.file, required=required or None, upstream=upstream or None)

    if findings:
        for finding in findings:
            print(finding)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
