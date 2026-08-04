"""Golden-reference regression gate for Flow artifacts.

Loads a hand-authored golden reference case and scores a candidate artifact
directory against it.  Exits non-zero when the candidate scores below the
configured min_overall threshold.

Usage:
    python -m flow_aidlc.checks.reference_check <case_dir> <candidate_dir>

    <case_dir>      — directory containing baseline.yaml and golden/
    <candidate_dir> — directory produced by a live Flow-run to score

    Prints per-file overalls, mean_overall, and PASS / FAIL.
    Exits 0 on PASS, 1 on FAIL (regression below threshold).

CI self-consistency smoke:
    Score the golden against itself — identical texts yield 1.0 everywhere,
    so this proves the scorer and the fixture are both well-formed with no
    LLM or network required:

        python -m flow_aidlc.checks.reference_check \\
            reference-runs/add-readonly-endpoint \\
            reference-runs/add-readonly-endpoint/golden

    The candidate path is `.../golden` (NOT `.../golden/shape`): score_dirs
    pairs files by path relative to each root, and the golden root already
    contains `shape/design.md`, so the candidate root must be the sibling
    `golden/` for the relative paths to match.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from flow_aidlc.checks.scorer import score_dirs


def check(case_dir: Path | str, candidate_dir: Path | str) -> dict:
    """Score candidate_dir against the golden inside case_dir.

    Loads ``<case_dir>/baseline.yaml`` to get ``min_overall``.
    Scores ``candidate_dir`` vs ``<case_dir>/golden`` using ``scorer.score_dirs``.

    Returns:
        {
            "passed": bool,
            "mean_overall": float,
            "min_overall": float,
            "per_file": {<relpath>: <score_docs dict>, ...},
        }
    """
    case_dir = Path(case_dir)
    candidate_dir = Path(candidate_dir)

    # -- load baseline --
    baseline_path = case_dir / "baseline.yaml"
    if yaml is None:
        raise RuntimeError(
            "pyyaml is required for reference_check; install it with: pip install pyyaml"
        )
    raw = yaml.safe_load(baseline_path.read_text(encoding="utf-8")) or {}
    min_overall: float = float(raw.get("min_overall", 0.75))

    # -- score candidate vs golden --
    golden_dir = case_dir / "golden"
    result = score_dirs(golden_dir, candidate_dir)

    mean_overall: float = result["mean_overall"]
    per_file: dict = result["per_file"]
    passed: bool = mean_overall >= min_overall

    return {
        "passed": passed,
        "mean_overall": mean_overall,
        "min_overall": min_overall,
        "per_file": per_file,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI: python -m flow_aidlc.checks.reference_check <case_dir> <candidate_dir>

    Exits 0 on PASS, 1 on FAIL.
    """
    args = (argv or sys.argv)[1:]
    if len(args) < 2:
        print(
            "Usage: python -m flow_aidlc.checks.reference_check <case_dir> <candidate_dir>",
            file=sys.stderr,
        )
        return 1

    case_dir = Path(args[0])
    candidate_dir = Path(args[1])

    result = check(case_dir, candidate_dir)
    per_file = result["per_file"]

    if not per_file:
        print("(no common files found between golden and candidate)")
    else:
        for relpath, scores in sorted(per_file.items()):
            print(f"  {relpath:60s}  overall={scores['overall']:.4f}")

    status = "PASS" if result["passed"] else "FAIL"
    print(
        f"mean_overall: {result['mean_overall']:.4f}  "
        f"(threshold: {result['min_overall']:.2f})  {status}"
    )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
