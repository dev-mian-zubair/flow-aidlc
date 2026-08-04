"""Detect doc drift by comparing knowledge-map.yaml entries against git history.

For each entry in .flow/knowledge-map.yaml:
  - Read the doc's ``verified-at-sha`` from YAML frontmatter.
  - Run ``git log --oneline <sha>..HEAD -- <globs>`` (subprocess list form).
  - If that range is non-empty (or sha is missing), the doc is STALE.

Usage:
    python -m flow_aidlc.checks.freshness           # exits 1 if any stale
    python -m flow_aidlc.checks.freshness --warn    # exits 0 even if stale (pre-push)
    python -m flow_aidlc.checks.freshness <repo>
    python -m flow_aidlc.checks.freshness <repo> --warn
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from flow_aidlc.checks._root import find_repo_root

try:
    import yaml  # pyyaml
except ImportError:
    yaml = None  # type: ignore[assignment]

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _read_verified_sha(doc_path: Path) -> Optional[str]:
    """Return the ``verified-at-sha`` from YAML frontmatter, or None if absent."""
    if not doc_path.exists():
        return None
    text = doc_path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None
    fm_text = m.group(1)
    if yaml is not None:
        try:
            fm = yaml.safe_load(fm_text)
            if isinstance(fm, dict):
                return fm.get("verified-at-sha")
        except Exception:
            pass
    # Fallback: simple line scan
    for line in fm_text.splitlines():
        if line.startswith("verified-at-sha:"):
            return line.split(":", 1)[1].strip()
    return None


def _git_log_range(repo_root: Path, sha: str, globs: list[str]) -> list[str]:
    """Return commit lines in <sha>..HEAD touching any of the globs."""
    cmd = ["git", "log", "--oneline", f"{sha}..HEAD", "--"] + globs
    result = subprocess.run(
        cmd, cwd=repo_root, capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def check(repo_root: Path | str) -> list[str]:
    """Return a list of stale doc paths (relative strings), or [] if all fresh."""
    repo_root = Path(repo_root)
    map_file = repo_root / ".flow" / "knowledge-map.yaml"
    if not map_file.exists():
        return []

    if yaml is None:
        raise ImportError("pyyaml is required: pip install pyyaml")

    data = yaml.safe_load(map_file.read_text(encoding="utf-8"))
    maps = data.get("maps", []) if data else []

    stale: list[str] = []
    for entry in maps:
        doc_rel: str = entry.get("doc", "")
        derives: list[str] = entry.get("derives-from", [])
        if not doc_rel:
            continue

        doc_path = repo_root / doc_rel
        sha = _read_verified_sha(doc_path)

        if sha is None:
            # No verified-at-sha → treat as stale
            stale.append(doc_rel)
            continue

        commits = _git_log_range(repo_root, sha, derives)
        if commits:
            stale.append(doc_rel)

    return stale


def main(argv: list[str] | None = None) -> int:
    args = (argv or sys.argv)[1:]
    warn_mode = "--warn" in args
    positional = [a for a in args if not a.startswith("--")]

    repo_root = Path(positional[0]) if positional else find_repo_root()

    stale = check(repo_root)
    if stale:
        prefix = "freshness WARNING" if warn_mode else "freshness FAILED"
        print(f"{prefix}: the following docs may be out of date:")
        for doc in stale:
            print(f"  STALE: {doc}")
        if not warn_mode:
            return 1
    else:
        print("freshness OK: all docs are up to date")

    return 0


if __name__ == "__main__":
    sys.exit(main())
