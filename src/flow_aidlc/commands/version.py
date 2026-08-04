from __future__ import annotations

from flow_aidlc import __version__


def run(argv: list[str]) -> int:
    print(f"flow {__version__}")
    return 0
