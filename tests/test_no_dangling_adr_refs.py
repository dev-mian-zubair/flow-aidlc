"""Guard against reintroducing ADR references in the shipped engine.

The Flow engine is scaffolded into a consumer's repo by `flow init`. That repo
has no `docs/flow/knowledge/decisions/NNNN-*.md` ADR files, so any dangling ADR link (a
`decisions/NNNN` path) or bare `ADR NNNN` mention in an engine markdown file is
a broken reference for every consumer. The decision was to inline the rationale
and drop ADR references entirely; this test makes a regression impossible.
"""
import re
from pathlib import Path

# tests/ -> package root; the shipped engine lives under src/flow_aidlc/engine/.
_ENGINE_DIR = Path(__file__).resolve().parents[1] / "src" / "flow_aidlc" / "engine"

# A dangling ADR markdown link (path fragment) or a bare "ADR NNNN" prose token.
_ADR_PATTERN = re.compile(r"decisions/[0-9]{4}|ADR [0-9]{4}")


def test_engine_has_zero_dangling_adr_refs():
    """No engine file may reference an ADR that a scaffolded repo won't have."""
    assert _ENGINE_DIR.is_dir(), f"engine dir not found: {_ENGINE_DIR}"

    offenders = []
    for path in sorted(_ENGINE_DIR.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            # Binary or unreadable file — no textual ADR refs to worry about.
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in _ADR_PATTERN.finditer(line):
                rel = path.relative_to(_ENGINE_DIR)
                offenders.append(f"{rel}:{lineno}: {match.group(0)!r}")

    assert not offenders, (
        "Found dangling ADR reference(s) in the engine — inline the rationale "
        "and drop the ADR tag (a scaffolded repo has no docs/flow/knowledge/decisions/ ADRs):\n"
        + "\n".join(offenders)
    )
