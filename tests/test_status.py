"""Tests for `flow status` — pipeline dashboard from worklog/progress.md."""
from pathlib import Path

from flow_aidlc.commands import status

_PROGRESS = """# Progress — {ticket}

## Scope
- [x] clarify
- [x] story
- [x] publish

## Shape
- [x] map-existing
- [ ] requirements
- [ ] design
- [ ] slicing

## Build
### Slice S1: thing
- [ ] slice-design

## Ship
- [ ] branch-hardening
"""


def _worklog(root: Path, ticket: str, text: str | None = None) -> None:
    d = root / "docs/flow/worklog" / ticket
    d.mkdir(parents=True, exist_ok=True)
    (d / "progress.md").write_text(text if text is not None else _PROGRESS.format(ticket=ticket))


def test_no_worklog_dir(tmp_path, capsys):
    assert status.run(["--path", str(tmp_path)]) == 0
    assert "no worklog" in capsys.readouterr().out.lower()


def test_empty_worklog(tmp_path, capsys):
    (tmp_path / "docs/flow/worklog").mkdir(parents=True)
    assert status.run(["--path", str(tmp_path)]) == 0
    assert "No worklogs yet" in capsys.readouterr().out


def test_reports_current_stage_and_progress(tmp_path, capsys):
    _worklog(tmp_path, "PI-7")
    assert status.run(["--path", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "PI-7" in out
    assert "Shape" in out           # current phase
    assert "requirements" in out    # first unchecked stage
    assert "4/9" in out             # 4 done of 9 stages


def test_complete_ticket(tmp_path, capsys):
    _worklog(tmp_path, "PI-9", "# Progress — PI-9\n\n## Scope\n- [x] clarify\n")
    status.run(["--path", str(tmp_path)])
    out = capsys.readouterr().out
    assert "complete" in out
    assert "1/1" in out


def test_ignores_dot_dirs_and_falls_back_to_dirname(tmp_path, capsys):
    # a hidden dir is skipped
    (tmp_path / "docs/flow/worklog" / ".active").mkdir(parents=True)
    # a progress file with an unfilled placeholder header falls back to the dir name
    _worklog(tmp_path, "PI-3", "# Progress — [Task ID]\n\n## Scope\n- [ ] clarify\n")
    status.run(["--path", str(tmp_path)])
    out = capsys.readouterr().out
    assert "PI-3" in out
    assert ".active" not in out
