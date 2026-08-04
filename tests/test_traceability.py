"""Tests for flow_aidlc.checks.traceability — deterministic requirement/slice coverage."""
from flow_aidlc.checks.traceability import (
    parse_requirement_ids,
    parse_slice_coverage,
    trace,
    check_task,
)

REQS = "## Functional\n- **FR-1** — a\n- **FR-2** — b\n## NFR\n| NFR-1 | x | y | z |\n"
SLICES_FULL = (
    "### Slice S1: first\n**Requirement refs:** FR-1, NFR-1\n\n---\n"
    "### Slice S2: second\n**Requirement refs:** FR-2\n"
)
SLICES_ORPHAN_REQ = "### Slice S1: first\n**Requirement refs:** FR-1\n"          # FR-2, NFR-1 uncovered
SLICES_ORPHAN_SLICE = (
    "### Slice S1: first\n**Requirement refs:** FR-1, FR-2, NFR-1\n\n---\n"
    "### Slice S2: stray\n**Requirement refs:** none\n"                          # cites no known ID
)


def test_parse_requirement_ids_finds_fr_and_nfr():
    assert parse_requirement_ids(REQS) == {"FR-1", "FR-2", "NFR-1"}


def test_parse_slice_coverage_maps_slice_to_refs():
    cov = parse_slice_coverage(SLICES_FULL)
    assert cov == {"S1": {"FR-1", "NFR-1"}, "S2": {"FR-2"}}


def test_full_coverage_has_no_orphans():
    r = trace(REQS, SLICES_FULL)
    assert r["orphan_requirements"] == [] and r["orphan_slices"] == []


def test_uncovered_requirement_is_orphan():
    r = trace(REQS, SLICES_ORPHAN_REQ)
    assert "FR-2" in r["orphan_requirements"] and "NFR-1" in r["orphan_requirements"]


def test_slice_citing_no_known_requirement_is_orphan_slice():
    r = trace(REQS, SLICES_ORPHAN_SLICE)
    assert r["orphan_slices"] == ["S2"]


def test_check_task_missing_files_returns_finding_not_exception(tmp_path):
    findings = check_task(tmp_path)          # no shape/requirements.md
    assert findings and any("not found" in f for f in findings)


def test_check_task_reports_orphan_requirement(tmp_path):
    shape = tmp_path / "shape"; shape.mkdir()
    (shape / "requirements.md").write_text(REQS)
    (shape / "slices.md").write_text(SLICES_ORPHAN_REQ)
    findings = check_task(tmp_path)
    assert any("FR-2" in f for f in findings)
