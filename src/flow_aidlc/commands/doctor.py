from __future__ import annotations

from flow_aidlc.commands import staged


def run(argv: list[str]) -> int:
    return staged("doctor", "M4")
