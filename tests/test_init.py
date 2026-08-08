"""Tests for `flow init` — scaffolding a Flow instance into a target repo."""
import subprocess
from pathlib import Path

from flow_aidlc.checks import gate
from flow_aidlc.commands import init


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)


def test_init_scaffolds_and_gate_passes(tmp_path):
    """A fresh init produces a rendered, gate-passing Flow instance."""
    _git_init(tmp_path)

    rc = init.run(
        ["--yes", "--repo", "owner/name", "--id-prefix", "PI", "--path", str(tmp_path)]
    )
    assert rc == 0

    config = tmp_path / ".flow" / "config.yaml"
    assert config.exists()
    config_text = config.read_text(encoding="utf-8")
    assert "owner/name" in config_text
    assert "PI-{n}" in config_text
    assert "{{" not in config_text, "unrendered tokens remain in config.yaml"

    # Core scaffolded files exist.
    assert (tmp_path / ".flow" / "playbook.md").exists()
    assert (tmp_path / ".claude" / "commands").is_dir()
    assert (tmp_path / ".claude" / "hooks" / "session-start.sh").exists()
    assert (tmp_path / "knowledge" / "map" / "README.md").exists()
    assert (tmp_path / ".mcp.json").exists()

    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".superpowers/" in gitignore

    # The quality gate passes against the freshly scaffolded instance.
    assert gate.run(tmp_path) == 0


def test_init_refuses_existing_without_force(tmp_path):
    """A second init over an existing .flow/ needs --force."""
    _git_init(tmp_path)

    assert init.run(["--yes", "--path", str(tmp_path)]) == 0
    # Without --force: refuse.
    assert init.run(["--yes", "--path", str(tmp_path)]) == 1
    # With --force: re-scaffold.
    assert init.run(["--yes", "--force", "--path", str(tmp_path)]) == 0


def test_init_dry_run_writes_nothing(tmp_path):
    """--dry-run reports success but leaves the target untouched."""
    _git_init(tmp_path)

    assert init.run(["--yes", "--dry-run", "--path", str(tmp_path)]) == 0
    assert not (tmp_path / ".flow").exists()


def test_init_scaffolds_env_example_with_tracker_vars(tmp_path):
    _git_init(tmp_path)
    assert init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)]) == 0
    example = (tmp_path / ".env.example").read_text()
    assert "GITHUB_TOKEN=" in example


def test_init_gitignores_dot_env(tmp_path):
    _git_init(tmp_path)
    init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)])
    assert ".env" in (tmp_path / ".gitignore").read_text().splitlines()


def test_init_does_not_create_real_dot_env(tmp_path):
    _git_init(tmp_path)
    init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)])
    assert not (tmp_path / ".env").exists()
