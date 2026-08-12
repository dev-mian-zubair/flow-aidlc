"""Gate: compose guardrail_lint + structure_check + reference-selfcheck + config-consistency + product-consistency.

Runs all five checks, prints a section per check, exits 1 if any blocking
check fails. The reference self-consistency smoke (CHECK 3/5) is
non-fatal-if-absent (no reference cases found → OK) but fatal-if-regressed
(a golden case scoring below its own threshold → exit 1).

Structural doc freshness (`knowledge-map.yaml` / `verified-at-sha` / freshness.py)
was RETIRED per ADR 0008: code *structure* now lives in the code graph
(fresh-by-construction), and the thinned `knowledge/map/` docs hold only
*invariants*, whose freshness is enforced by the always-on guardrails
(`enforced-by:`) at Build/verify — not by a stale-flag here.

Usage:
    python -m flow_aidlc.checks.gate               # uses repo root
    python -m flow_aidlc.checks.gate <repo_root>
    python -m flow_aidlc.checks.gate --strict      # accepted for compatibility (no-op)
"""
from __future__ import annotations

import sys
from pathlib import Path

from flow_aidlc.checks._root import find_repo_root
from flow_aidlc.checks.guardrail_lint import lint as guardrail_lint
from flow_aidlc.checks.structure_check import check as structure_check
from flow_aidlc.checks.reference_check import check as reference_check
from flow_aidlc.checks.config_consistency import check as config_consistency_check
from flow_aidlc.checks.product_consistency import check as product_consistency_check


def run(repo_root: Path | str, strict_freshness: bool = False) -> int:
    """Run all checks; return 0 if all pass, 1 if any fail.

    ``strict_freshness`` is retained for signature/CLI compatibility (structural
    freshness is retired — see the module docstring) and is ignored.
    """
    repo_root = Path(repo_root)
    flow_dir = repo_root / ".flow"
    guardrails_dir = flow_dir / "guardrails"
    exit_code = 0

    # ---- 1. Guardrail lint ----
    print("=" * 60)
    print("CHECK 1/5  guardrail-lint")
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
    print("CHECK 2/5  structure-check")
    print("=" * 60)
    struct_errors = structure_check(flow_dir)
    if struct_errors:
        print("FAILED:")
        for e in struct_errors:
            print(f"  {e}")
        exit_code = 1
    else:
        print("OK")

    # ---- 3. Reference self-consistency smoke ----
    print()
    print("=" * 60)
    print("CHECK 3/5  reference-selfcheck")
    print("=" * 60)
    selfcheck_failed = _run_reference_selfcheck(repo_root)
    if selfcheck_failed:
        exit_code = 1

    # ---- 4. Config consistency ----
    print()
    print("=" * 60)
    print("CHECK 4/5  config-consistency")
    print("=" * 60)
    cfg_errors = config_consistency_check(repo_root)
    if cfg_errors:
        print("FAILED:")
        for e in cfg_errors:
            print(f"  {e}")
        exit_code = 1
    else:
        print("OK")

    # ---- 5. Product consistency ----
    print()
    print("=" * 60)
    print("CHECK 5/5  product-consistency")
    print("=" * 60)
    product_errors = product_consistency_check(repo_root)
    if product_errors:
        print("FAILED:")
        for e in product_errors:
            print(f"  {e}")
        exit_code = 1
    else:
        print("OK")

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
