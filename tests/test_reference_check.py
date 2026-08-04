"""Tests for flow_aidlc.checks.reference_check — TDD.

Uses the real golden fixture at reference-runs/add-readonly-endpoint to
ensure the checker and fixture are wired together correctly.

Two key tests:
  1. Golden vs itself (self-consistency) → passed is True, mean_overall ~= 1.0.
  2. Degraded candidate (content gutted) → passed is False.
"""
from pathlib import Path

import pytest

# Locate the fixture directory relative to the test file (scripts/flow-checks/)
_FLOW_CHECKS_DIR = Path(__file__).resolve().parents[1]
_CASE_DIR = _FLOW_CHECKS_DIR / "reference-runs" / "add-readonly-endpoint"
_GOLDEN_DIR = _CASE_DIR / "golden"


# ---------------------------------------------------------------------------
# Self-consistency smoke: golden scored against itself → PASS
# ---------------------------------------------------------------------------

def test_check_golden_vs_itself_passes():
    """check(case, case/golden/shape) — golden scored against itself → passed True."""
    from flow_aidlc.checks.reference_check import check

    result = check(_CASE_DIR, _GOLDEN_DIR)

    assert result["passed"] is True, (
        f"Golden vs itself should pass; got {result}"
    )
    assert result["mean_overall"] == pytest.approx(1.0), (
        f"Golden vs itself should be mean_overall=1.0, got {result['mean_overall']}"
    )


def test_check_golden_vs_itself_loads_min_overall():
    """check() correctly loads min_overall from baseline.yaml."""
    from flow_aidlc.checks.reference_check import check

    result = check(_CASE_DIR, _GOLDEN_DIR)

    assert result["min_overall"] == pytest.approx(0.75), (
        f"Expected min_overall=0.75 from baseline.yaml, got {result['min_overall']}"
    )


def test_check_result_contains_per_file():
    """check() result always includes per_file dict."""
    from flow_aidlc.checks.reference_check import check

    result = check(_CASE_DIR, _GOLDEN_DIR)

    assert "per_file" in result, f"Missing 'per_file' key in result: {result}"
    assert len(result["per_file"]) > 0, "Expected at least one file in per_file"


# ---------------------------------------------------------------------------
# Degraded candidate → FAIL
# ---------------------------------------------------------------------------

def test_check_degraded_candidate_fails(tmp_path):
    """A candidate with gutted content scores below threshold → passed is False."""
    from flow_aidlc.checks.reference_check import check

    # Copy golden to a candidate dir, then gut one file's content
    cand_dir = tmp_path / "degraded"
    cand_dir.mkdir()

    # Write near-empty versions of all golden files (different filenames/content
    # would score 0 on all dimensions)
    golden_files = list(_GOLDEN_DIR.rglob("*.md"))
    assert golden_files, "Golden dir must have at least one .md file"

    for gf in golden_files:
        rel = gf.relative_to(_GOLDEN_DIR)
        dest = cand_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Write a near-empty stub — completely disjoint vocab, no headings
        dest.write_text("placeholder text only\n")

    result = check(_CASE_DIR, cand_dir)

    assert result["passed"] is False, (
        f"Degraded candidate should fail; got mean_overall={result['mean_overall']}, "
        f"min_overall={result['min_overall']}, passed={result['passed']}"
    )
    assert result["mean_overall"] < result["min_overall"], (
        f"mean_overall ({result['mean_overall']}) should be < min_overall ({result['min_overall']})"
    )


# ---------------------------------------------------------------------------
# Return value contract
# ---------------------------------------------------------------------------

def test_check_returns_all_required_keys():
    """check() always returns passed, mean_overall, min_overall, per_file."""
    from flow_aidlc.checks.reference_check import check

    result = check(_CASE_DIR, _GOLDEN_DIR)

    for key in ("passed", "mean_overall", "min_overall", "per_file"):
        assert key in result, f"Missing key '{key}' in result: {result}"


def test_check_passed_is_bool():
    """check() 'passed' value is a proper bool."""
    from flow_aidlc.checks.reference_check import check

    result = check(_CASE_DIR, _GOLDEN_DIR)
    assert isinstance(result["passed"], bool), (
        f"'passed' should be bool, got {type(result['passed'])}"
    )
