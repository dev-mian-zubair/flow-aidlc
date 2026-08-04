"""Deterministic learnings extractor for Flow task journals.

Scans a task's journal.md for correction/redirection signals and surfaces
candidate learnings for human curation.  Also provides an idempotent helper
to append approved learnings to knowledge/practices.md.

Offline, no LLM, no network.  Adopted from AWS AI-DLC's learnings ritual.

Usage:
    python -m flow_aidlc.checks.learnings <task_dir> [--practices <path>]

Exits 0 always (advisory — the human curates and appends).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SIGNAL_WORDS = (
    "actually",
    "instead",
    "should have",
    "don't",
    "do not",
    "revert",
    "prefer",
    "wrong",
    "mistake",
    "correction",
    "redirect",
)

_AGENT_PREFIXES = ("[agent] blocker", "[agent] graduated")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_candidates(journal_text: str) -> list[str]:
    """Return candidate learnings from *journal_text*.

    Splits on ``## `` datetime headers.  For each entry body, scans (case-
    insensitive) for any SIGNAL_WORD or ``[agent] Blocker/Graduated`` prefix.
    When matched, the body's first non-empty line (stripped) is collected.
    Order is preserved; exact-duplicate lines are removed.
    """
    # Split on "## " headers — keep everything after the header
    parts = re.split(r"^## ", journal_text, flags=re.MULTILINE)
    # parts[0] is anything before the first header (usually empty)

    seen: set[str] = set()
    results: list[str] = []

    for part in parts[1:]:  # skip pre-header preamble
        # The header text is on the first line; the body follows
        lines = part.splitlines()
        body_lines = lines[1:]  # skip the header timestamp line itself
        body = "\n".join(body_lines)
        body_lower = body.lower()

        matched = False

        # Check signal words
        for word in SIGNAL_WORDS:
            if word in body_lower:
                matched = True
                break

        # Check [agent] prefixes
        if not matched:
            body_stripped_lower = body.strip().lower()
            for prefix in _AGENT_PREFIXES:
                if body_stripped_lower.startswith(prefix):
                    matched = True
                    break

        if matched:
            # Collect the first non-empty line from the body
            for line in body_lines:
                stripped = line.strip()
                if stripped:
                    if stripped not in seen:
                        seen.add(stripped)
                        results.append(stripped)
                    break

    return results


def slug(candidate: str) -> str:
    """Return a deterministic, offline slug for *candidate*.

    Takes the first six lowercase alphanumeric words joined by hyphens.
    """
    return "-".join(re.findall(r"[a-z0-9]+", candidate.lower())[:6])


def existing_markers(practices_text: str) -> set[str]:
    """Return the set of practice marker IDs already present in *practices_text*."""
    return set(re.findall(r"<!--\s*practice-marker:\s*(\S+)\s*-->", practices_text))


def append_practice(
    practices_text: str,
    title: str,
    body: str,
    why: str,
    source: str,
) -> str:
    """Append a new practice block to *practices_text* and return the result.

    Idempotent: if the marker derived from *title* + *body* already exists in
    *practices_text*, the text is returned unchanged.

    The next ``P-N`` id is ``max(existing ids) + 1``, or 1 if none exist.
    """
    marker = slug(title + " " + body)
    if marker in existing_markers(practices_text):
        return practices_text

    # Determine next P-N id
    existing_ids = [int(m) for m in re.findall(r"^## P-(\d+)\s", practices_text, re.MULTILINE)]
    next_id = max(existing_ids) + 1 if existing_ids else 1

    block = (
        f"\n## P-{next_id} — {title}\n"
        f"<!-- practice-marker: {marker} -->\n"
        f"\n"
        f"**Practice:** {body}\n"
        f"**Why:** {why}\n"
        f"**Source:** {source}\n"
    )
    return practices_text + block


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    python -m flow_aidlc.checks.learnings <task_dir> [--practices <path>]
    """
    parser = argparse.ArgumentParser(
        description="Extract candidate learnings from a task journal.",
    )
    parser.add_argument("task_dir", help="Path to the task directory (must contain journal.md).")
    parser.add_argument(
        "--practices",
        metavar="PATH",
        default=None,
        help="Path to knowledge/practices.md — marks which candidates are already recorded.",
    )

    parsed = parser.parse_args(argv if argv is not None else sys.argv[1:])

    journal_path = Path(parsed.task_dir) / "journal.md"
    if not journal_path.exists():
        print(f"[learnings] no journal at {journal_path} — nothing to extract.")
        return 0

    journal_text = journal_path.read_text(encoding="utf-8", errors="replace")
    candidates = extract_candidates(journal_text)

    # Optionally load existing markers so we can flag already-recorded ones
    already: set[str] = set()
    if parsed.practices:
        practices_path = Path(parsed.practices)
        if practices_path.exists():
            already = existing_markers(practices_path.read_text(encoding="utf-8", errors="replace"))

    if not candidates:
        print("[learnings] No correction/redirection signals found in journal.")
        return 0

    print("[learnings] Candidate practices (human curation required):\n")
    for i, candidate in enumerate(candidates, start=1):
        marker = slug(candidate)
        status = " [already recorded]" if marker in already else ""
        print(f"  {i}. {candidate}{status}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
