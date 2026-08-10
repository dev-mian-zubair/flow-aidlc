"""Tests for `flow learnings` — surface/promote candidate learnings."""
from pathlib import Path

from flow_aidlc.commands import learnings

_JOURNAL = """# Journal

## 2026-08-08T10:00:00Z · build/generate
We actually should have used a queue here instead of a cron loop.

## 2026-08-08T11:00:00Z · build/verify
Routine stage close, nothing notable.
"""


def _worklog(root: Path, ticket: str, journal: str) -> None:
    d = root / "docs/flow/worklog" / ticket
    d.mkdir(parents=True, exist_ok=True)
    (d / "journal.md").write_text(journal)


def test_no_candidates(tmp_path, capsys):
    _worklog(tmp_path, "PI-1", "# Journal\n\n## t · s\nNothing to see.\n")
    assert learnings.run(["--path", str(tmp_path)]) == 0
    assert "No candidate learnings" in capsys.readouterr().out


def test_lists_new_candidate(tmp_path, capsys):
    _worklog(tmp_path, "PI-2", _JOURNAL)
    assert learnings.run(["--path", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "NEW" in out
    assert "queue" in out
    assert "PI-2" in out


def test_promote_appends_to_practices(tmp_path):
    _worklog(tmp_path, "PI-2", _JOURNAL)
    practices = tmp_path / "docs/flow/knowledge" / "practices.md"
    assert learnings.run(["--promote", "--path", str(tmp_path)]) == 0
    assert practices.exists()
    text = practices.read_text()
    assert "queue" in text
    assert "practice-marker:" in text
    assert "docs/flow/worklog/PI-2" in text  # source attribution


def test_promote_is_idempotent(tmp_path):
    _worklog(tmp_path, "PI-2", _JOURNAL)
    learnings.run(["--promote", "--path", str(tmp_path)])
    practices = tmp_path / "docs/flow/knowledge" / "practices.md"
    first = practices.read_text()
    learnings.run(["--promote", "--path", str(tmp_path)])
    assert practices.read_text() == first  # no duplicate block


def test_recorded_candidate_not_flagged_new(tmp_path, capsys):
    _worklog(tmp_path, "PI-2", _JOURNAL)
    learnings.run(["--promote", "--path", str(tmp_path)])
    capsys.readouterr()
    learnings.run(["--path", str(tmp_path)])
    out = capsys.readouterr().out
    assert "0 new" in out
