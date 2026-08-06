"""Tests for `flow setup` — portable one-command onboarding.

`setup --dry-run` must print the planned chain and exit 0 without requiring any
external tool (uv / the graph binary), so it is safe to run in CI on a bare repo.
"""
import subprocess
from pathlib import Path

from flow_aidlc.commands import init, setup


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)


def test_setup_dry_run_prints_chain_and_exits_zero(tmp_path, capsys):
    """A fresh init followed by `setup --dry-run` prints the chain and returns 0."""
    _git_init(tmp_path)
    assert init.run(["--yes", "--repo", "owner/name", "--id-prefix", "PI", "--path", str(tmp_path)]) == 0

    rc = setup.run(["--path", str(tmp_path), "--dry-run"])
    assert rc == 0

    out = capsys.readouterr().out
    # The onboarding chain is announced: graph tool -> graph build -> doctor.
    assert "Flow setup" in out
    assert "flow doctor" in out
    # Dry-run must not have run anything external.
    assert "dry-run" in out.lower()


def test_setup_without_flow_dir_fails(tmp_path):
    """`flow setup` needs an initialised .flow/ — it errors clearly without one."""
    _git_init(tmp_path)
    assert setup.run(["--path", str(tmp_path), "--dry-run"]) == 1
