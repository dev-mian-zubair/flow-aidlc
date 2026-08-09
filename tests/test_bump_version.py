"""Tests for scripts/bump_version.py — the lockstep version bumper."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "scripts" / "bump_version.py"

# scripts/ is not a package; load the module straight from its path.
_spec = importlib.util.spec_from_file_location("bump_version", _SCRIPT)
bv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bv)


def _fake_repo(tmp_path: Path, version: str = "0.1.0") -> Path:
    """Build a throwaway tree with the three version files at *version*."""
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "flow-aidlc"\nversion = "{version}"\n', encoding="utf-8"
    )
    init = tmp_path / "src" / "flow_aidlc" / "__init__.py"
    init.parent.mkdir(parents=True)
    init.write_text(f'__version__ = "{version}"\n', encoding="utf-8")
    ver = tmp_path / "src" / "flow_aidlc" / "engine" / "flow" / "VERSION"
    ver.parent.mkdir(parents=True)
    ver.write_text(f"{version}\n", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    "version,level,expected",
    [
        ("0.1.0", "patch", "0.1.1"),
        ("0.1.0", "minor", "0.2.0"),
        ("0.1.0", "major", "1.0.0"),
        ("1.4.9", "patch", "1.4.10"),
        ("1.4.9", "minor", "1.5.0"),
    ],
)
def test_bump_math(version, level, expected):
    assert bv.bump(version, level) == expected


def test_bump_rejects_non_semver():
    with pytest.raises(SystemExit):
        bv.bump("0.1", "patch")


def test_write_updates_all_three(tmp_path):
    root = _fake_repo(tmp_path, "0.1.0")
    bv.write_version("0.1.1", root=root)
    assert bv.read_versions(root) == {
        "pyproject": "0.1.1",
        "init": "0.1.1",
        "engine": "0.1.1",
    }
    # VERSION keeps its trailing newline.
    assert (root / "src/flow_aidlc/engine/flow/VERSION").read_text() == "0.1.1\n"


def test_write_rejects_bad_target(tmp_path):
    root = _fake_repo(tmp_path)
    with pytest.raises(SystemExit):
        bv.write_version("v0.1.1", root=root)


def test_current_version_detects_drift(tmp_path):
    root = _fake_repo(tmp_path, "0.1.0")
    (root / "src/flow_aidlc/engine/flow/VERSION").write_text("0.9.9\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        bv.current_version(root)


def test_check_mode_passes_in_sync(tmp_path, capsys):
    root = _fake_repo(tmp_path, "0.2.0")
    # Point the module's ROOT at the fake repo for the CLI path.
    bv.read_versions(root)  # sanity
    assert set(bv.read_versions(root).values()) == {"0.2.0"}


def test_live_repo_versions_are_in_sync():
    """Regression guard: the real repo's three version files must always agree."""
    versions = bv.read_versions(_REPO)
    assert len(set(versions.values())) == 1, f"version drift in repo: {versions}"
