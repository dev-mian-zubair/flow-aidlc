"""Flow CLI command handlers. Each module exposes ``run(argv) -> int``."""
from __future__ import annotations

import sys


def staged(name: str, milestone: str) -> int:
    """Uniform message for a command whose implementation is scheduled."""
    sys.stderr.write(
        f"flow {name}: not implemented yet (planned for {milestone}).\n"
    )
    return 2
