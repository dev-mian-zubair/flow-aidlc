"""`flow learnings` — surface (and optionally promote) candidate learnings.

Scans ``worklog/<id>/journal.md`` for correction/redirection signals (via the
offline extractor in ``flow_aidlc.checks.learnings``) and lists candidate
learnings not yet recorded in ``knowledge/practices.md``. With ``--promote`` it
appends the new ones (idempotent). Curation stays a human decision — the default
is read-only surfacing.

Usage:
    flow learnings [--promote] [--path DIR]
"""
from __future__ import annotations

import argparse
from pathlib import Path

from flow_aidlc.checks import learnings as L
from flow_aidlc.checks._root import find_repo_root


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="flow learnings", description="Surface candidate learnings from journals.")
    p.add_argument("--promote", action="store_true", help="Append the new candidates to knowledge/practices.md.")
    p.add_argument("--path", default=None, help="Repo dir (default: search up from cwd).")
    return p


def run(argv: list[str]) -> int:
    try:
        args = _parser().parse_args(argv)
    except SystemExit:
        return 2
    root = find_repo_root(args.path)
    worklog = root / "worklog"
    practices = root / "knowledge" / "practices.md"
    ptext = practices.read_text(encoding="utf-8") if practices.exists() else ""
    recorded = L.existing_markers(ptext)

    found: list[tuple[str, str, str, bool]] = []  # (ticket, candidate, marker, is_new)
    if worklog.is_dir():
        for d in sorted(worklog.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            journal = d / "journal.md"
            if not journal.exists():
                continue
            for cand in L.extract_candidates(journal.read_text(encoding="utf-8")):
                marker = L.slug(cand + " " + cand)  # matches append_practice(title=body=cand)
                found.append((d.name, cand, marker, marker not in recorded))

    if not found:
        print("No candidate learnings found in worklog journals.")
        return 0

    new = [f for f in found if f[3]]

    if args.promote:
        added = 0
        for ticket, cand, _marker, _is_new in new:
            before = ptext
            ptext = L.append_practice(ptext, cand, cand, "surfaced from a task journal", f"worklog/{ticket}")
            if ptext != before:
                added += 1
        practices.parent.mkdir(parents=True, exist_ok=True)
        practices.write_text(ptext, encoding="utf-8")
        print(f"Promoted {added} new learning(s) to {practices.relative_to(root)}.")
        return 0

    print(
        f"Candidate learnings — {len(new)} new / {len(found)} total. "
        "Use `flow learnings --promote` to record the new ones.\n"
    )
    for ticket, cand, _marker, is_new in found:
        print(f"  [{'NEW' if is_new else '  •'}] {ticket}: {cand}")
    return 0
