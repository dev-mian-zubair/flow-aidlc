"""Tests for guardrail starter packs — `flow guardrail packs` / `add --from`."""
import subprocess
from pathlib import Path

from flow_aidlc.checks.guardrail_lint import lint
from flow_aidlc.commands import guardrail, init


def _repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    assert init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)]) == 0
    return tmp_path


def test_packs_lists_web_api(capsys):
    assert guardrail.run(["packs"]) == 0
    out = capsys.readouterr().out
    assert "web-api" in out
    assert "authz-on-mutations" in out


def test_add_from_pack_installs_registers_and_lints_clean(tmp_path):
    _repo(tmp_path)
    assert guardrail.run(["add", "--from", "web-api", "--path", str(tmp_path)]) == 0
    gdir = tmp_path / ".flow" / "guardrails" / "always-on"
    for name in ("authz-on-mutations", "input-validation", "no-hardcoded-secrets"):
        assert (gdir / f"{name}.md").exists()
    cfg = (tmp_path / ".flow" / "config.yaml").read_text()
    assert "authz-on-mutations" in cfg
    # The installed pack must pass guardrail_lint (sections present, IDs unique).
    assert lint(tmp_path / ".flow" / "guardrails") == []


def test_add_from_pack_optional_targets_optional_dir(tmp_path):
    _repo(tmp_path)
    guardrail.run(["add", "--from", "web-api", "--optional", "--path", str(tmp_path)])
    assert (tmp_path / ".flow" / "guardrails" / "optional" / "authz-on-mutations.md").exists()
    assert not (tmp_path / ".flow" / "guardrails" / "always-on" / "authz-on-mutations.md").exists()


def test_unknown_pack_errors(tmp_path):
    _repo(tmp_path)
    assert guardrail.run(["add", "--from", "does-not-exist", "--path", str(tmp_path)]) == 2


def test_reinstall_skips_existing(tmp_path, capsys):
    _repo(tmp_path)
    guardrail.run(["add", "--from", "web-api", "--path", str(tmp_path)])
    capsys.readouterr()
    assert guardrail.run(["add", "--from", "web-api", "--path", str(tmp_path)]) == 0
    assert "Skipped" in capsys.readouterr().out
