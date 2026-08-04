"""Gate: compose guardrail_lint + structure_check + freshness + reference-selfcheck.

Runs all four checks, prints a section per check, exits 1 if any blocking
check fails.  Freshness runs in warn-mode (non-blocking) by default so doc
drift doesn't hard-block CI — structure and lint are the blocking checks.
The reference self-consistency smoke (CHECK 4/4) is non-fatal-if-absent (no
reference cases found → OK) but fatal-if-regressed (a golden case scoring
below its own threshold → exit 1).

Usage:
    python -m flow_aidlc.checks.gate               # uses repo root
    python -m flow_aidlc.checks.gate <repo_root>
    python -m flow_aidlc.checks.gate --strict      # freshness is also blocking
"""
from __future__ import annotations

import sys
from pathlib import Path

from flow_aidlc.checks._root import find_repo_root
from flow_aidlc.checks.guardrail_lint import lint as guardrail_lint
from flow_aidlc.checks.structure_check import check as structure_check
from flow_aidlc.checks.freshness import check as freshness_check
from flow_aidlc.checks.reference_check import check as reference_check


def run(repo_root: Path | str, strict_freshness: bool = False) -> int:
    """Run all checks; return 0 if all pass, 1 if any fail."""
    repo_root = Path(repo_root)
    flow_dir = repo_root / ".flow"
    guardrails_dir = flow_dir / "guardrails"
    exit_code = 0

    # ---- 1. Guardrail lint ----
    print("=" * 60)
    print("CHECK 1/4  guardrail-lint")
    print("=" * 60)
    lint_errors = guardrail_lint(guardrails_dir)
    if lint_errors:
        print("FAILED:")
        for e in lint_errors:
            print(f"  {e}")
        exit_code = 1
    else:
        print("OK")

    # ---- 2. Structure check ----
    print()
    print("=" * 60)
    print("CHECK 2/4  structure-check")
    print("=" * 60)
    struct_errors = structure_check(flow_dir)
    if struct_errors:
        print("FAILED:")
        for e in struct_errors:
            print(f"  {e}")
        exit_code = 1
    else:
        print("OK")

    # ---- 3. Freshness ----
    print()
    print("=" * 60)
    print("CHECK 3/4  freshness")
    print("=" * 60)
    stale = freshness_check(repo_root)
    if stale:
        label = "FAILED" if strict_freshness else "WARNING (non-blocking)"
        print(f"{label}: stale docs:")
        for doc in stale:
            print(f"  STALE: {doc}")
        if strict_freshness:
            exit_code = 1
    else:
        print("OK: all docs are up to date")

    # ---- 4. Reference self-consistency smoke ----
    print()
    print("=" * 60)
    print("CHECK 4/4  reference-selfcheck")
    print("=" * 60)
    selfcheck_failed = _run_reference_selfcheck(repo_root)
    if selfcheck_failed:
        exit_code = 1

    print()
    if exit_code == 0:
        print("gate PASSED")
    else:
        print("gate FAILED")
    return exit_code


def _run_reference_selfcheck(repo_root: Path) -> bool:
    """Run reference self-consistency smoke for each case under reference-runs/.

    Non-fatal-if-absent: no reference-runs dir or no cases → print OK, return False.
    Fatal-if-regressed: any golden case scoring below its own threshold → return True.

    Returns True if any case failed (caller should set exit_code = 1).
    """
    # reference-runs/ lives at <repo_root>/scripts/flow-checks/reference-runs.
    # Derive it from the passed repo_root so a non-default root is honored.
    ref_runs_dir = repo_root / "scripts" / "flow-checks" / "reference-runs"

    if not ref_runs_dir.exists():
        print("OK: no reference cases (reference-runs/ not found)")
        return False

    cases = [
        p for p in ref_runs_dir.iterdir()
        if p.is_dir()
        and (p / "baseline.yaml").exists()
        and (p / "golden").exists()
    ]

    if not cases:
        print("OK: no reference cases")
        return False

    any_failed = False
    for case_dir in sorted(cases):
        golden_dir = case_dir / "golden"
        result = reference_check(case_dir, golden_dir)
        status = "PASS" if result["passed"] else "FAIL"
        print(
            f"  {case_dir.name:40s}  mean_overall={result['mean_overall']:.4f}  "
            f"(threshold={result['min_overall']:.2f})  {status}"
        )
        if not result["passed"]:
            any_failed = True

    if any_failed:
        print("FAILED: one or more reference cases regressed below their threshold")
    else:
        print("OK: all reference cases pass self-consistency smoke")
    return any_failed


def main(argv: list[str] | None = None) -> int:
    args = (argv or sys.argv)[1:]
    strict = "--strict" in args
    positional = [a for a in args if not a.startswith("--")]
    repo_root = Path(positional[0]) if positional else find_repo_root()
    return run(repo_root, strict_freshness=strict)


if __name__ == "__main__":
    sys.exit(main())
