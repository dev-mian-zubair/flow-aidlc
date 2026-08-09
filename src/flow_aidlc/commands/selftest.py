"""`flow selftest` — run the engine's own vendored check-suite unit tests.

This is the engine's self-test: it invokes pytest over the vendored
``tests/`` directory (the unit tests for the quality-gate check modules). It is
distinct from the in-repo wiring self-test, which lands later. If pytest is not
importable, we point the user at the dev extra rather than crashing.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _find_tests_dir() -> Path | None:
    """Locate the vendored tests/ dir relative to this package.

    Layout: ``<root>/src/flow_aidlc/commands/selftest.py`` with the tests at
    ``<root>/tests``. Walk up from this file looking for a ``tests`` dir that
    sits beside a ``src`` dir (the package root), falling back to any ``tests``
    dir found on the way up.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "tests"
        if cand.is_dir() and (parent / "src").is_dir():
            return cand
    # Fallback: first tests/ dir found walking up.
    for parent in here.parents:
        cand = parent / "tests"
        if cand.is_dir():
            return cand
    return None


def run(argv: list[str]) -> int:
    try:
        import pytest  # noqa: F401
    except ImportError:
        sys.stderr.write(
            "flow selftest: pytest is not installed.\n"
            "Install the dev extra:  pip install flow-aidlc[dev]\n"
        )
        return 2

    tests_dir = _find_tests_dir()
    if tests_dir is None:
        sys.stderr.write(
            "flow selftest: no vendored tests/ directory found — this command runs the\n"
            "engine's own unit suite and only works from a source checkout, not an\n"
            "installed package. To verify an installed instance, use `flow check`\n"
            "(the quality gate) and `flow doctor` (install + integration health).\n"
        )
        return 2

    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(tests_dir), *argv]
    )
    return completed.returncode
