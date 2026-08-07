"""Deterministic requirement-to-slice traceability check.

Parses stable requirement IDs (FR-N / NFR-N) from a task's requirements.md and
each slice's requirement refs from slices.md, then reports:

- orphan requirements  — no slice covers them  → exit 1
- orphan slices        — cite no known requirement → warning only, exit 0

Cross-phase traceability verification.  Offline / deterministic:
no LLM, no network, no eval, no random, no time.

Usage:
    python -m flow_aidlc.checks.traceability <task_dir>
    python -m flow_aidlc.checks.traceability <task_dir> --write
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_ID_RE = re.compile(r"\b(?:FR|NFR)-\d+\b")


# ---------------------------------------------------------------------------
# Pure parsing helpers
# ---------------------------------------------------------------------------

def parse_requirement_ids(text: str) -> set[str]:
    """Return all FR-N / NFR-N tokens found in *text*."""
    return set(_ID_RE.findall(text))


def parse_slice_coverage(text: str) -> dict[str, set[str]]:
    """Return a mapping of slice_id -> set of requirement IDs it cites.

    Slices are delimited by ``### Slice `` headers.  The slice_id is the
    token before the first ``:`` in the header remainder.
    """
    coverage: dict[str, set[str]] = {}
    # Split on "### Slice " — each element after index 0 starts with the
    # header remainder (everything after "### Slice ").
    parts = text.split("### Slice ")
    for part in parts[1:]:
        # First line is the header remainder, rest is the block body.
        newline = part.find("\n")
        if newline == -1:
            header_remainder = part
            block_body = ""
        else:
            header_remainder = part[:newline]
            block_body = part[newline + 1:]

        m = re.match(r"(\S+):", header_remainder)
        if not m:
            continue
        slice_id = m.group(1)
        refs = set(_ID_RE.findall(block_body))
        coverage[slice_id] = refs
    return coverage


# ---------------------------------------------------------------------------
# Core trace engine
# ---------------------------------------------------------------------------

def trace(requirements_text: str, slices_text: str) -> dict:
    """Return a traceability result dict with keys:

    - ``req_ids``              — set[str] of all requirement IDs found
    - ``coverage``             — dict[str, set[str]] slice_id → cited req IDs
    - ``covered``              — set[str] union of all cited req IDs
    - ``orphan_requirements``  — sorted list of req_ids with no covering slice
    - ``orphan_slices``        — sorted list of slice IDs that cite no known req
    - ``matrix``               — {req_id: [slice_ids covering it]} sorted
    """
    req_ids = parse_requirement_ids(requirements_text)
    coverage = parse_slice_coverage(slices_text)

    # Guard the empty-coverage case to avoid set().union(*[]) crash.
    if coverage:
        covered: set[str] = set().union(*coverage.values())
    else:
        covered = set()

    orphan_requirements = sorted(req_ids - covered)
    orphan_slices = sorted(
        sid for sid, refs in coverage.items() if not (refs & req_ids)
    )
    matrix = {
        rid: sorted(sid for sid, refs in coverage.items() if rid in refs)
        for rid in sorted(req_ids)
    }

    return {
        "req_ids": req_ids,
        "coverage": coverage,
        "covered": covered,
        "orphan_requirements": orphan_requirements,
        "orphan_slices": orphan_slices,
        "matrix": matrix,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_matrix(result: dict) -> str:
    """Render a markdown coverage matrix table from a ``trace()`` result."""
    matrix: dict[str, list[str]] = result.get("matrix", {})
    lines = [
        "| Requirement | Covered by | Status |",
        "| --- | --- | --- |",
    ]
    for rid, slices in matrix.items():
        covered_by = ", ".join(slices) if slices else "—"
        status = "ok" if slices else "ORPHAN"
        lines.append(f"| {rid} | {covered_by} | {status} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Task-level check
# ---------------------------------------------------------------------------

def check_task(task_dir: Path | str) -> list[str]:
    """Check traceability for the task rooted at *task_dir*.

    Reads ``<task_dir>/shape/requirements.md`` and ``<task_dir>/shape/slices.md``.
    Returns a list of finding strings (empty → all clear).  Never raises.
    """
    task_dir = Path(task_dir)
    shape_dir = task_dir / "shape"
    req_path = shape_dir / "requirements.md"
    slices_path = shape_dir / "slices.md"

    findings: list[str] = []

    if not req_path.exists():
        findings.append(f"traceability: {req_path} not found")
    if not slices_path.exists():
        findings.append(f"traceability: {slices_path} not found")

    if findings:
        return findings

    req_text = req_path.read_text(encoding="utf-8", errors="replace")
    slices_text = slices_path.read_text(encoding="utf-8", errors="replace")

    result = trace(req_text, slices_text)

    for rid in result["orphan_requirements"]:
        findings.append(f"orphan requirement (no slice covers it): {rid}")
    for sid in result["orphan_slices"]:
        findings.append(f"orphan slice (cites no known requirement): {sid}")

    return findings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    python -m flow_aidlc.checks.traceability <task_dir>
    python -m flow_aidlc.checks.traceability <task_dir> --write
    """
    parser = argparse.ArgumentParser(
        description="Traceability check: requirement IDs vs. slice coverage.",
    )
    parser.add_argument("task_dir", help="Path to the task directory (contains shape/).")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the coverage matrix to task_dir/shape/traceability.md.",
    )

    parsed = parser.parse_args(argv if argv is not None else sys.argv[1:])
    task_dir = Path(parsed.task_dir)
    shape_dir = task_dir / "shape"
    req_path = shape_dir / "requirements.md"
    slices_path = shape_dir / "slices.md"

    # Read files (gracefully handle missing).
    missing: list[str] = []
    if not req_path.exists():
        missing.append(f"traceability: {req_path} not found")
    if not slices_path.exists():
        missing.append(f"traceability: {slices_path} not found")

    if missing:
        for m in missing:
            print(m)
        return 1

    req_text = req_path.read_text(encoding="utf-8", errors="replace")
    slices_text = slices_path.read_text(encoding="utf-8", errors="replace")

    result = trace(req_text, slices_text)
    matrix_md = render_matrix(result)

    # Print orphan requirements as errors.
    has_orphan_reqs = bool(result["orphan_requirements"])
    for rid in result["orphan_requirements"]:
        print(f"ERROR: orphan requirement (no slice covers it): {rid}")

    # Print orphan slices as warnings (do not affect exit code).
    for sid in result["orphan_slices"]:
        print(f"WARNING: orphan slice (cites no known requirement): {sid}")

    print()
    print(matrix_md)

    if parsed.write:
        out_path = shape_dir / "traceability.md"
        lines = ["# Traceability Matrix\n", matrix_md, ""]
        if result["orphan_requirements"]:
            lines.append("\n## Orphan Requirements\n")
            for rid in result["orphan_requirements"]:
                lines.append(f"- {rid}: no slice covers this requirement")
        if result["orphan_slices"]:
            lines.append("\n## Orphan Slices\n")
            for sid in result["orphan_slices"]:
                lines.append(f"- {sid}: cites no known requirement")
        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nWrote {out_path}")

    # Exit 1 if any orphan requirement; orphan slices are warnings only.
    return 1 if has_orphan_reqs else 0


if __name__ == "__main__":
    sys.exit(main())
