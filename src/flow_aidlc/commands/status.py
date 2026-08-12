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
from flow_aidlc.paths import PRODUCT_DIR, WORKLOG_DIR

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
    worklog = root / WORKLOG_DIR
    if not worklog.is_dir():
        print("no worklog dir (docs/flow/worklog) — run `flow init` first")
    else:
        rows = []
        for d in sorted(worklog.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            progress = d / "progress.md"
            if progress.exists():
                rows.append(_summarize(d, progress.read_text(encoding="utf-8")))
        if not rows:
            print("No worklogs yet — start one with `/flow-scope`.")
        else:
            _print_table(rows)

    _print_product(root)
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


def _product_row(text: str) -> tuple[str, str, str, int, int]:
    """Parse a product unit's progress.md → (id, kind, status, checked, total)."""
    fm: dict[str, str] = {}
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for ln in lines[1:]:
            if ln.strip() == "---":
                break
            if ":" in ln:
                k, _, v = ln.partition(":")
                v = v.strip()
                cut = v.find(" #")          # strip inline YAML comment (space + #)
                if cut != -1:
                    v = v[:cut].rstrip()
                fm[k.strip()] = v
    checked = total = 0
    for ln in lines:
        m = _STAGE_RE.match(ln)
        if m:
            total += 1
            if m.group(1).lower() == "x":
                checked += 1
    return fm.get("id", "?"), fm.get("kind", "?"), fm.get("status", "?"), checked, total


def _print_product(root: Path) -> None:
    """List Discover product workstreams — additive, only when the dir exists."""
    product = root / PRODUCT_DIR
    if not product.is_dir():
        return
    units = []
    for d in sorted(product.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        prog = d / "progress.md"
        if prog.exists():
            units.append(_product_row(prog.read_text(encoding="utf-8")))
    if not units:
        return
    print("\nDiscover / product workstreams")
    print(f"{'ID':<20}  {'KIND':<12}  {'STATUS':<20}  STAGES")
    for uid, kind, st, checked, total in units:
        bar = f"{checked}/{total}" if total else "-"
        print(f"{uid:<20}  {kind:<12}  {st:<20}  {bar}")
