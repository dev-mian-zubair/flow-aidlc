"""Tests for `flow upgrade` — refresh engine assets, never touch the instance."""
import subprocess
from pathlib import Path

from flow_aidlc import __version__
from flow_aidlc.checks import gate
from flow_aidlc.commands import guardrail, init, upgrade
from flow_aidlc.engine_assets import engine_dir


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)


def _init_repo(tmp_path: Path) -> None:
    _git_init(tmp_path)
    rc = init.run(
        ["--yes", "--repo", "owner/name", "--id-prefix", "PI", "--path", str(tmp_path)]
    )
    assert rc == 0


def test_upgrade_replaces_engine_preserves_instance(tmp_path):
    """Upgrade restores a drifted engine file while leaving instance files intact."""
    _init_repo(tmp_path)
    tmp = str(tmp_path)

    # (a) Simulate an old install by rewinding the recorded engine version.
    (tmp_path / ".flow" / "VERSION").write_text("0.0.1\n", encoding="utf-8")

    # (b) Corrupt an ENGINE file — the playbook — to prove it gets restored.
    playbook = tmp_path / ".flow" / "playbook.md"
    playbook.write_text("STALE", encoding="utf-8")

    # (c) Author an INSTANCE file (a project guardrail) and record its bytes.
    assert guardrail.run(["add", "my-inv", "--prefix", "MY", "--path", tmp]) == 0
    my_inv = tmp_path / ".flow" / "guardrails" / "always-on" / "my-inv.md"
    my_inv_bytes = my_inv.read_bytes()

    # ...and edit the rendered instance config to carry a user marker.
    config = tmp_path / ".flow" / "config.yaml"
    config.write_text(config.read_text(encoding="utf-8") + "\n# USER EDIT\n", encoding="utf-8")

    assert upgrade.run(["--path", tmp]) == 0

    # Engine file restored — matches the packaged playbook, no longer "STALE".
    engine_playbook = (engine_dir() / "flow" / "playbook.md").read_text(encoding="utf-8")
    assert playbook.read_text(encoding="utf-8") != "STALE"
    assert playbook.read_text(encoding="utf-8") == engine_playbook

    # Instance guardrail is byte-identical (never overwritten).
    assert my_inv.read_bytes() == my_inv_bytes

    # User's config edits + registration survive.
    config_text = config.read_text(encoding="utf-8")
    assert "# USER EDIT" in config_text
    assert "my-inv" in config_text

    # VERSION now records the package version.
    assert (tmp_path / ".flow" / "VERSION").read_text(encoding="utf-8").strip() == __version__

    # The gate still passes against the upgraded instance.
    assert gate.run(tmp_path) == 0


def test_upgrade_noop_when_current(tmp_path):
    """A fresh install is already current — upgrade reports so and changes nothing."""
    _init_repo(tmp_path)
    tmp = str(tmp_path)

    playbook = tmp_path / ".flow" / "playbook.md"
    before = playbook.read_bytes()

    assert upgrade.run(["--path", tmp]) == 0

    assert playbook.read_bytes() == before
    assert (tmp_path / ".flow" / "VERSION").read_text(encoding="utf-8").strip() == __version__


def test_upgrade_dry_run_writes_nothing(tmp_path):
    """--dry-run leaves a corrupted engine file untouched and still returns 0."""
    _init_repo(tmp_path)
    tmp = str(tmp_path)

    # Rewind version so upgrade would otherwise act, then corrupt the playbook.
    (tmp_path / ".flow" / "VERSION").write_text("0.0.1\n", encoding="utf-8")
    playbook = tmp_path / ".flow" / "playbook.md"
    playbook.write_text("STALE", encoding="utf-8")

    assert upgrade.run(["--dry-run", "--path", tmp]) == 0

    assert playbook.read_text(encoding="utf-8") == "STALE"
    # VERSION untouched under dry-run.
    assert (tmp_path / ".flow" / "VERSION").read_text(encoding="utf-8").strip() == "0.0.1"


def test_upgrade_not_a_flow_repo(tmp_path):
    """Outside a Flow repo, upgrade explains and returns 2."""
    assert upgrade.run(["--path", str(tmp_path)]) == 2
