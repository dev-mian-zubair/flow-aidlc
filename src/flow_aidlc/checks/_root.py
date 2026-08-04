from __future__ import annotations
from pathlib import Path

def find_repo_root(start: Path | str | None = None) -> Path:
    """Walk up from `start` (default: cwd) to the first dir containing `.flow/`.
    Fall back to `start` if none found."""
    p = Path(start or Path.cwd()).resolve()
    for cand in (p, *p.parents):
        if (cand / ".flow").is_dir():
            return cand
    return p
