"""Tests for flow_aidlc.checks.learnings — TDD."""
from flow_aidlc.checks.learnings import (
    extract_candidates, slug, existing_markers, append_practice,
)

JOURNAL = (
    "## 2026-08-04T10:00:00Z\n\nStage Shape/design complete.\n\n"        # neutral → excluded
    "## 2026-08-04T10:05:00Z\n\nActually, use the existing BudgetService instead of a new one.\n\n"
    "## 2026-08-04T10:10:00Z\n\n[agent] Blocker: SpiceDB check missing on the new route.\n"
)


def test_extract_candidates_picks_corrections_not_neutral():
    cands = extract_candidates(JOURNAL)
    assert any("BudgetService" in c for c in cands)
    assert any("Blocker" in c for c in cands)
    assert not any("Shape/design complete" in c for c in cands)


def test_slug_is_deterministic_and_stable():
    assert slug("Use the existing BudgetService") == slug("use the existing budgetservice")


def test_existing_markers_parses_marker_comments():
    text = "## P-1 — x\n<!-- practice-marker: use-existing-service -->\n"
    assert existing_markers(text) == {"use-existing-service"}


def test_append_practice_is_idempotent():
    base = "# Practices\n"
    once = append_practice(base, "Reuse services", "Prefer existing services", "avoids drift", "PI-1")
    twice = append_practice(once, "Reuse services", "Prefer existing services", "avoids drift", "PI-1")
    assert once == twice                                # same marker → no duplicate
    assert once.count("<!-- practice-marker:") == 1
    assert "## P-1 —" in once


def test_append_practice_increments_id():
    base = "# Practices\n"
    one = append_practice(base, "A", "aa", "w", "PI-1")
    two = append_practice(one, "B", "bb", "w", "PI-2")
    assert "## P-1 —" in two and "## P-2 —" in two
