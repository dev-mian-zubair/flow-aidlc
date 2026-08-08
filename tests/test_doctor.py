"""Tests for `flow doctor`'s skill-pack check.

The check reads Claude Code's ``installed_plugins.json`` via ``CLAUDE_CONFIG_DIR``
so it is fully unit-testable: point that env var at a temp dir with a crafted
manifest. The check must never FAIL (doctor runs in CI, where no manifest
exists) — a missing pack or an unverifiable manifest is a WARN.
"""
import json
from pathlib import Path

from flow_aidlc.commands import doctor


def _write_manifest(config_dir: Path, plugins: dict) -> None:
    """Write a minimal installed_plugins.json under a fake CLAUDE_CONFIG_DIR."""
    manifest = config_dir / "plugins" / "installed_plugins.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"version": 2, "plugins": plugins}), encoding="utf-8")


# ---------------------------------------------------------------------------
# _installed_plugin_names — the detection helper
# ---------------------------------------------------------------------------

def test_missing_manifest_returns_none(tmp_path, monkeypatch):
    """No manifest (e.g. CI, or not a Claude Code env) → cannot verify → None."""
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    assert doctor._installed_plugin_names(tmp_path) is None


def test_unparseable_manifest_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    manifest = tmp_path / "plugins" / "installed_plugins.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("{not json", encoding="utf-8")
    assert doctor._installed_plugin_names(tmp_path) is None


def test_user_scope_plugin_is_available(tmp_path, monkeypatch):
    """A user-scope (global) install counts regardless of the repo path."""
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    _write_manifest(tmp_path, {
        "superpowers@claude-plugins-official": [{"scope": "user"}],
    })
    names = doctor._installed_plugin_names(tmp_path)
    assert names is not None and "superpowers" in names


def test_project_scope_matches_only_this_repo(tmp_path, monkeypatch):
    """A project-scope install counts only for its own projectPath."""
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    repo = tmp_path / "repo"
    repo.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    _write_manifest(tmp_path, {
        "pr-review-toolkit@claude-plugins-official": [
            {"scope": "project", "projectPath": str(other)},
        ],
    })
    # Installed only for `other` — not available for `repo`.
    assert "pr-review-toolkit" not in (doctor._installed_plugin_names(repo) or set())
    # Available for its own project.
    assert "pr-review-toolkit" in (doctor._installed_plugin_names(other) or set())


# ---------------------------------------------------------------------------
# _check_skills — the reported line
# ---------------------------------------------------------------------------

def test_check_skills_warns_when_manifest_absent(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    rep = doctor._Report()
    doctor._check_skills(rep, tmp_path)
    out = capsys.readouterr().out
    assert "[WARN]" in out and "skills" in out
    assert rep.any_fail is False  # never fails the verdict


def test_check_skills_passes_when_both_installed(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    _write_manifest(tmp_path, {
        "superpowers@claude-plugins-official": [{"scope": "user"}],
        "pr-review-toolkit@obra-marketplace": [{"scope": "user"}],
    })
    rep = doctor._Report()
    doctor._check_skills(rep, tmp_path)
    out = capsys.readouterr().out
    assert "[PASS]" in out and "superpowers" in out
    assert rep.any_fail is False


def test_check_skills_warns_on_partial_install(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    _write_manifest(tmp_path, {
        "superpowers@claude-plugins-official": [{"scope": "user"}],
    })
    rep = doctor._Report()
    doctor._check_skills(rep, tmp_path)
    out = capsys.readouterr().out
    assert "[WARN]" in out and "pr-review-toolkit" in out
    assert rep.any_fail is False


# ---------------------------------------------------------------------------
# _check_secrets — the reported line
# ---------------------------------------------------------------------------

def _mcp_repo(tmp_path):
    (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {
        "github": {"command": "npx", "args": ["-y", "srv"],
                    "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}}}}, indent=2))
    return tmp_path


def test_check_secrets_warns_when_unset(tmp_path, monkeypatch, capsys):
    _mcp_repo(tmp_path)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    rep = doctor._Report()
    doctor._check_secrets(rep, tmp_path)
    out = capsys.readouterr().out
    assert "[WARN]" in out and "secrets" in out
    assert rep.any_fail is False  # never FAIL


def test_check_secrets_pass_when_set(tmp_path, monkeypatch, capsys):
    _mcp_repo(tmp_path)
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    rep = doctor._Report()
    doctor._check_secrets(rep, tmp_path)
    assert "[PASS]" in capsys.readouterr().out
    assert rep.any_fail is False
