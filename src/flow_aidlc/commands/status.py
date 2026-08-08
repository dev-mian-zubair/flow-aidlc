"""`flow status` — where each ticket sits in the Scope→Shape→Build→Ship pipeline.

Reads each ``worklog/<id>/progress.md`` (the checkbox stage list) and reports the
current stage and completion per ticket. Read-only — it surfaces the state Flow
already records, it never edits it.

Usage:
    flow status [--path DIR]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from flow_aidlc.checks._root import find_repo_root

_PHASES = ("Scope", "Shape", "Build", "Ship")
_STAGE_RE = re.compile(r"^\s*- \[([ xX])\]\s+(.+?)\s*$")
_ID_RE = re.compile(r"^#\s+Progress\s+—\s+(.+?)\s*$", re.MULTILINE)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="flow status", description="Show pipeline status per ticket.")
    p.add_argument("--path", default=None, help="Repo dir (default: search up from cwd).")
    return p


def run(argv: list[str]) -> int:
    try:
        args = _parser().parse_args(argv)
    except SystemExit:
        return 2
    root = find_repo_root(args.path)
    worklog = root / "worklog"
    if not worklog.is_dir():
        print("no worklog/ here — run `flow init` first")
        return 0

    rows = []
    for d in sorted(worklog.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        progress = d / "progress.md"
        if progress.exists():
            rows.append(_summarize(d, progress.read_text(encoding="utf-8")))

    if not rows:
        print("No worklogs yet — start one with `/flow-scope`.")
        return 0
    _print_table(rows)
    return 0


def _parse_stages(text: str) -> list[tuple[str, str, bool]]:
    """Return ``(phase, stage, done)`` for every checkbox under a known phase."""
    phase: str | None = None
    stages: list[tuple[str, str, bool]] = []
    for line in text.splitlines():
        if line.startswith("## "):
            head = line[3:].strip()
            phase = head if head in _PHASES else None
            continue
        m = _STAGE_RE.match(line)
        if m and phase:
            stages.append((phase, m.group(2).strip(), m.group(1).lower() == "x"))
    return stages


def _summarize(directory: Path, text: str) -> dict:
    m = _ID_RE.search(text)
    ticket = m.group(1).strip() if m else directory.name
    if not ticket or ticket.startswith("["):  # unfilled placeholder header
        ticket = directory.name

    stages = _parse_stages(text)
    total = len(stages)
    done = sum(1 for *_r, ok in stages if ok)
    nxt = next((s for s in stages if not s[2]), None)
    if nxt:
        phase, stage = nxt[0], nxt[1]
    elif total:
        phase, stage = "Ship", "complete ✓"
    else:
        phase, stage = "—", "—"
    return {"ticket": ticket, "phase": phase, "stage": stage, "done": done, "total": total}


def _print_table(rows: list[dict]) -> None:
    w = max([len(r["ticket"]) for r in rows] + [len("TICKET")])
    print(f"{'TICKET':<{w}}  {'PHASE':<6}  {'CURRENT STAGE':<16}  PROGRESS")
    for r in rows:
        bar = f"{r['done']}/{r['total']}" if r["total"] else "-"
        print(f"{r['ticket']:<{w}}  {r['phase']:<6}  {r['stage']:<16}  {bar}")
