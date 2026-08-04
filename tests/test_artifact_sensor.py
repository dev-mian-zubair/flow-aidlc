"""Tests for flow_aidlc.checks.artifact_sensor — TDD."""
from pathlib import Path


# ---------------------------------------------------------------------------
# required_sections
# ---------------------------------------------------------------------------

def test_required_sections_all_present_returns_empty():
    """All required headings present → []."""
    from flow_aidlc.checks.artifact_sensor import required_sections

    text = "## Rule\nsome content\n## Verification\nmore content\n"
    result = required_sections(text, ["## Rule", "## Verification"])
    assert result == [], f"Expected [], got {result}"


def test_required_sections_one_missing():
    """One heading absent → that heading returned."""
    from flow_aidlc.checks.artifact_sensor import required_sections

    text = "## Rule\nsome content\n"
    result = required_sections(text, ["## Rule", "## Verification"])
    assert result == ["## Verification"], f"Expected ['## Verification'], got {result}"


def test_required_sections_all_missing():
    """No required headings present → all returned."""
    from flow_aidlc.checks.artifact_sensor import required_sections

    text = "# Intro\nNo required sections here.\n"
    result = required_sections(text, ["## Rule", "## Verification"])
    assert "## Rule" in result
    assert "## Verification" in result
    assert len(result) == 2


def test_required_sections_empty_required_list():
    """Empty required list → always []."""
    from flow_aidlc.checks.artifact_sensor import required_sections

    result = required_sections("anything", [])
    assert result == []


def test_required_sections_heading_prefix_match():
    """A heading with trailing text (e.g. '## Rule: detail') is still matched."""
    from flow_aidlc.checks.artifact_sensor import required_sections

    text = "## Rule: specific rule detail\nContent.\n"
    result = required_sections(text, ["## Rule"])
    assert result == [], f"Expected [], got {result}"


# ---------------------------------------------------------------------------
# upstream_coverage
# ---------------------------------------------------------------------------

def test_upstream_coverage_all_cited_returns_empty():
    """All upstream names present in text → []."""
    from flow_aidlc.checks.artifact_sensor import upstream_coverage

    text = "See requirements.md for details and design.md for context."
    result = upstream_coverage(text, ["requirements.md", "design.md"])
    assert result == [], f"Expected [], got {result}"


def test_upstream_coverage_one_missing():
    """One upstream not cited → that name returned."""
    from flow_aidlc.checks.artifact_sensor import upstream_coverage

    text = "See requirements.md for details."
    result = upstream_coverage(text, ["requirements.md", "design.md"])
    assert result == ["design.md"], f"Expected ['design.md'], got {result}"


def test_upstream_coverage_case_insensitive():
    """Citation match is case-insensitive."""
    from flow_aidlc.checks.artifact_sensor import upstream_coverage

    text = "Based on REQUIREMENTS.MD and the docs."
    result = upstream_coverage(text, ["requirements.md"])
    assert result == [], f"Expected [], got {result}"


def test_upstream_coverage_all_missing():
    """No upstream names cited → all returned."""
    from flow_aidlc.checks.artifact_sensor import upstream_coverage

    text = "No references here."
    result = upstream_coverage(text, ["requirements.md", "design.md"])
    assert "requirements.md" in result
    assert "design.md" in result
    assert len(result) == 2


def test_upstream_coverage_empty_upstream_list():
    """Empty upstream list → always []."""
    from flow_aidlc.checks.artifact_sensor import upstream_coverage

    result = upstream_coverage("anything", [])
    assert result == []


# ---------------------------------------------------------------------------
# sense
# ---------------------------------------------------------------------------

def test_sense_clean_file_returns_empty(tmp_path: Path):
    """File with all sections and upstream citations → []."""
    from flow_aidlc.checks.artifact_sensor import sense

    f = tmp_path / "artifact.md"
    f.write_text(
        "## Rule\nAll rules here.\n## Verification\nSee requirements.md.\n",
        encoding="utf-8",
    )
    result = sense(f, required=["## Rule", "## Verification"], upstream=["requirements.md"])
    assert result == [], f"Expected [], got {result}"


def test_sense_missing_section_and_upstream(tmp_path: Path):
    """File missing a section and upstream citation → both findings present."""
    from flow_aidlc.checks.artifact_sensor import sense

    f = tmp_path / "artifact.md"
    f.write_text("## Rule\nContent only.\n", encoding="utf-8")
    result = sense(
        f,
        required=["## Rule", "## Verification"],
        upstream=["requirements.md"],
    )
    assert any("## Verification" in r for r in result), \
        f"Expected missing section finding, got {result}"
    assert any("requirements.md" in r for r in result), \
        f"Expected missing upstream finding, got {result}"


def test_sense_missing_section_finding_format(tmp_path: Path):
    """Missing section finding uses the expected prefix."""
    from flow_aidlc.checks.artifact_sensor import sense

    f = tmp_path / "artifact.md"
    f.write_text("No headings.\n", encoding="utf-8")
    result = sense(f, required=["## Rule"], upstream=None)
    assert any(r.startswith("missing section:") for r in result), \
        f"Expected 'missing section:' prefix, got {result}"


def test_sense_missing_upstream_finding_format(tmp_path: Path):
    """Missing upstream finding uses the expected prefix."""
    from flow_aidlc.checks.artifact_sensor import sense

    f = tmp_path / "artifact.md"
    f.write_text("Some content.\n", encoding="utf-8")
    result = sense(f, required=None, upstream=["requirements.md"])
    assert any(r.startswith("missing upstream citation:") for r in result), \
        f"Expected 'missing upstream citation:' prefix, got {result}"


def test_sense_nonexistent_path_returns_finding_no_exception(tmp_path: Path):
    """Nonexistent file → single 'file not found' finding, no exception."""
    from flow_aidlc.checks.artifact_sensor import sense

    missing = tmp_path / "does_not_exist.md"
    result = sense(missing, required=["## Rule"], upstream=["requirements.md"])
    assert len(result) == 1, f"Expected exactly 1 finding, got {result}"
    assert "file not found" in result[0], f"Expected 'file not found' in finding, got {result}"


def test_sense_none_args_defaults(tmp_path: Path):
    """sense with required=None, upstream=None → [] for any file (no checks run)."""
    from flow_aidlc.checks.artifact_sensor import sense

    f = tmp_path / "artifact.md"
    f.write_text("Anything.\n", encoding="utf-8")
    result = sense(f, required=None, upstream=None)
    assert result == [], f"Expected [], got {result}"
