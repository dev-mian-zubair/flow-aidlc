"""Tests for flow_aidlc.checks.scorer — TDD.

Behavior-asserting tests for the offline, deterministic reproducibility scorer.
No LLM or network calls; pure text math only.
"""
import math
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# score_docs — identical text
# ---------------------------------------------------------------------------

def test_score_docs_identical_text_overall_is_1():
    """Identical reference and candidate must yield overall == 1.0."""
    from flow_aidlc.checks.scorer import score_docs

    text = (
        "# My Heading\n\n"
        "## Sub Heading\n\n"
        "This document describes the UserService and budget_engine components.\n"
        "It uses check_resource_access and snake_case identifiers.\n"
    )
    result = score_docs(text, text)
    assert result["overall"] == pytest.approx(1.0), (
        f"identical texts must yield overall=1.0, got {result}"
    )
    assert result["intent"] == pytest.approx(1.0)
    assert result["design"] == pytest.approx(1.0)
    assert result["completeness"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# score_docs — completeness
# ---------------------------------------------------------------------------

def test_score_docs_missing_headings_reduces_completeness():
    """Candidate missing half the reference's headings → completeness < 1.0 and overall < 1.0."""
    from flow_aidlc.checks.scorer import score_docs

    reference = (
        "# Title\n\n"
        "## Functional Requirements\n\nSome functional stuff.\n\n"
        "## Non-Functional Requirements\n\nSome NFR stuff.\n\n"
        "## Out of Scope\n\nOut of scope things.\n\n"
        "## Design\n\nDesign details here.\n"
    )
    # candidate has only 2 of the 4 headings
    candidate = (
        "# Title\n\n"
        "## Functional Requirements\n\nSome functional stuff.\n\n"
        "Some other content without the other headings.\n"
    )
    result = score_docs(reference, candidate)
    assert result["completeness"] < 1.0, (
        f"completeness should be < 1.0 when headings are missing, got {result['completeness']}"
    )
    assert result["overall"] < 1.0, (
        f"overall should be < 1.0, got {result['overall']}"
    )


# ---------------------------------------------------------------------------
# score_docs — intent (unrelated texts → low similarity)
# ---------------------------------------------------------------------------

def test_score_docs_unrelated_texts_low_intent():
    """Two texts with disjoint vocabulary → intent < 0.3."""
    from flow_aidlc.checks.scorer import score_docs

    reference = (
        "## Database Schema\n\n"
        "The relational database stores rows tables columns indexes foreign keys.\n"
        "Schema migrations alembic upgrade head revision postgres.\n"
    )
    candidate = (
        "## Cooking Recipe\n\n"
        "Combine flour sugar butter eggs vanilla baking powder chocolate chips.\n"
        "Bake oven preheat temperature minutes cookies delicious.\n"
    )
    result = score_docs(reference, candidate)
    assert result["intent"] < 0.3, (
        f"unrelated texts should yield intent < 0.3, got {result['intent']}"
    )


# ---------------------------------------------------------------------------
# score_docs — weights sanity check
# ---------------------------------------------------------------------------

def test_score_docs_overall_weighted_correctly():
    """overall == 0.4*intent + 0.4*design + 0.2*completeness."""
    from flow_aidlc.checks.scorer import score_docs

    # Use identical texts so we know all components should be 1.0
    text = "## Section\n\nWords words words snake_case CamelCase.\n"
    result = score_docs(text, text)
    expected_overall = 0.4 * result["intent"] + 0.4 * result["design"] + 0.2 * result["completeness"]
    assert result["overall"] == pytest.approx(expected_overall, abs=1e-9), (
        f"overall={result['overall']} != 0.4*{result['intent']} + 0.4*{result['design']} + 0.2*{result['completeness']}"
    )


# ---------------------------------------------------------------------------
# score_dirs — matching files identical → mean_overall == 1.0
# ---------------------------------------------------------------------------

def test_score_dirs_identical_files_mean_overall_is_1(tmp_path):
    """score_dirs on two dirs with one matching identical file → mean_overall == 1.0."""
    from flow_aidlc.checks.scorer import score_dirs

    ref_dir = tmp_path / "ref"
    cand_dir = tmp_path / "cand"
    ref_dir.mkdir()
    cand_dir.mkdir()

    content = (
        "# Requirements\n\n"
        "## Functional Requirements\n\n"
        "The UserService must call check_resource_access before returning results.\n"
        "All budget reads come from the budgets table.\n"
    )
    (ref_dir / "requirements.md").write_text(content)
    (cand_dir / "requirements.md").write_text(content)

    result = score_dirs(ref_dir, cand_dir)
    assert result["mean_overall"] == pytest.approx(1.0), (
        f"identical files should yield mean_overall=1.0, got {result}"
    )
    assert "per_file" in result
    assert "requirements.md" in result["per_file"]


# ---------------------------------------------------------------------------
# score_dirs — no common files → mean_overall == 0.0
# ---------------------------------------------------------------------------

def test_score_dirs_no_common_files_mean_is_zero(tmp_path):
    """score_dirs with no overlapping file paths → mean_overall == 0.0."""
    from flow_aidlc.checks.scorer import score_dirs

    ref_dir = tmp_path / "ref"
    cand_dir = tmp_path / "cand"
    ref_dir.mkdir()
    cand_dir.mkdir()

    (ref_dir / "alpha.md").write_text("# Alpha\n\nReference only.\n")
    (cand_dir / "beta.md").write_text("# Beta\n\nCandidate only.\n")

    result = score_dirs(ref_dir, cand_dir)
    assert result["mean_overall"] == 0.0, (
        f"no common files should yield mean_overall=0.0, got {result['mean_overall']}"
    )
    assert result["per_file"] == {}


# ---------------------------------------------------------------------------
# score_dirs — subdirectory paths matched correctly
# ---------------------------------------------------------------------------

def test_score_dirs_matches_files_by_relative_path(tmp_path):
    """score_dirs pairs files by relative path, ignoring root differences."""
    from flow_aidlc.checks.scorer import score_dirs

    ref_dir = tmp_path / "ref"
    cand_dir = tmp_path / "cand"
    (ref_dir / "shape").mkdir(parents=True)
    (cand_dir / "shape").mkdir(parents=True)

    content = "# Design\n\n## Components\n\nThe UserService component.\n"
    (ref_dir / "shape" / "design.md").write_text(content)
    (cand_dir / "shape" / "design.md").write_text(content)

    # File only in ref — should NOT be in per_file
    (ref_dir / "shape" / "extra.md").write_text("# Extra\n")

    result = score_dirs(ref_dir, cand_dir)
    assert "shape/design.md" in result["per_file"], (
        f"expected shape/design.md in per_file, got keys: {list(result['per_file'].keys())}"
    )
    assert "shape/extra.md" not in result["per_file"]
    assert result["mean_overall"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# score_docs — empty reference headings → completeness 1.0
# ---------------------------------------------------------------------------

def test_score_docs_no_headings_in_reference_completeness_is_1():
    """When reference has no headings, completeness should be 1.0."""
    from flow_aidlc.checks.scorer import score_docs

    reference = "This is a flat document with no headings at all.\n"
    candidate = "This is also a flat document without headings.\n"
    result = score_docs(reference, candidate)
    assert result["completeness"] == pytest.approx(1.0), (
        f"no headings in reference → completeness=1.0, got {result['completeness']}"
    )


# ---------------------------------------------------------------------------
# score_docs — result keys always present
# ---------------------------------------------------------------------------

def test_score_docs_returns_all_required_keys():
    """score_docs must always return all four keys."""
    from flow_aidlc.checks.scorer import score_docs

    result = score_docs("# Hello\nworld\n", "# Hello\nworld\n")
    for key in ("intent", "design", "completeness", "overall"):
        assert key in result, f"Missing key '{key}' in result: {result}"
        assert 0.0 <= result[key] <= 1.0, f"Key '{key}' out of [0,1]: {result[key]}"


# ---------------------------------------------------------------------------
# score_docs — cosine clamp: real golden design.md self-score is EXACTLY 1.0
# ---------------------------------------------------------------------------

_FLOW_CHECKS_DIR = Path(__file__).resolve().parents[1]
_GOLDEN_DESIGN = (
    _FLOW_CHECKS_DIR
    / "reference-runs" / "add-readonly-endpoint" / "golden" / "shape" / "design.md"
)


def test_score_docs_real_golden_design_self_score_is_exactly_1():
    """The real golden design.md scored against itself must be EXACTLY 1.0.

    This is the regression test for the cosine clamp: this document has a large,
    repetitive vocabulary that made the un-clamped cosine return
    1.0000000000000002, so `overall` was only approx-1.0. With the clamp, every
    component and overall must be exactly 1.0 (== not approx), and no component
    may exceed 1.0.
    """
    from flow_aidlc.checks.scorer import score_docs

    text = _GOLDEN_DESIGN.read_text(encoding="utf-8")
    result = score_docs(text, text)

    # Exact equality — not pytest.approx — proves the clamp holds.
    assert result["intent"] == 1.0, f"intent must be exactly 1.0, got {result['intent']!r}"
    assert result["design"] == 1.0, f"design must be exactly 1.0, got {result['design']!r}"
    assert result["completeness"] == 1.0, (
        f"completeness must be exactly 1.0, got {result['completeness']!r}"
    )
    assert result["overall"] == 1.0, f"overall must be exactly 1.0, got {result['overall']!r}"

    # No component may exceed 1.0.
    for key, value in result.items():
        assert value <= 1.0, f"component {key} exceeds 1.0: {value!r}"
