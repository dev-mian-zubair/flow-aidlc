# tests/test_secrets.py
import json
import os
from pathlib import Path

from flow_aidlc.commands import secrets

def _write_mcp(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    mcp = {"mcpServers": {
        "github": {"command": "npx", "args": ["-y", "srv-github"],
                    "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}},
        "graphify": {"command": "graphify-mcp", "args": ["graph.json"]},
    }}
    (root / ".mcp.json").write_text(json.dumps(mcp, indent=2) + "\n")
    return root / ".mcp.json"

def _servers(path: Path):
    return json.loads(path.read_text())["mcpServers"]

def test_use_wraps_all_secret_servers_leaves_others(tmp_path):
    p = _write_mcp(tmp_path)
    assert secrets.run(["use", "infisical", "--path", str(tmp_path)]) == 0
    s = _servers(p)
    assert s["github"]["command"] == "infisical"
    assert s["github"]["args"][:3] == ["run", "--", "npx"]
    assert "_flowWrapped" in s["github"]
    assert s["graphify"]["command"] == "graphify-mcp"   # untouched
    assert "_flowWrapped" not in s["graphify"]

def test_use_is_idempotent(tmp_path):
    p = _write_mcp(tmp_path)
    secrets.run(["use", "infisical", "--path", str(tmp_path)])
    first = p.read_text()
    assert secrets.run(["use", "infisical", "--path", str(tmp_path)]) == 0
    assert p.read_text() == first

def test_off_restores_original(tmp_path):
    p = _write_mcp(tmp_path)
    before = p.read_text()
    secrets.run(["use", "infisical", "--path", str(tmp_path)])
    assert secrets.run(["off", "--path", str(tmp_path)]) == 0
    assert json.loads(p.read_text()) == json.loads(before)

def test_use_dry_run_writes_nothing(tmp_path):
    p = _write_mcp(tmp_path)
    before = p.read_text()
    assert secrets.run(["use", "infisical", "--dry-run", "--path", str(tmp_path)]) == 0
    assert p.read_text() == before

def test_use_env_flag_in_wrapper(tmp_path):
    p = _write_mcp(tmp_path)
    secrets.run(["use", "infisical", "--env", "prod", "--path", str(tmp_path)])
    assert _servers(p)["github"]["args"][:4] == ["run", "--env", "prod", "--"]

def test_unknown_provider_errors(tmp_path):
    _write_mcp(tmp_path)
    assert secrets.run(["use", "bogus", "--path", str(tmp_path)]) == 2

def test_guided_only_provider_prints_pattern(tmp_path, capsys):
    _write_mcp(tmp_path)
    assert secrets.run(["use", "doppler", "--path", str(tmp_path)]) == 2
    assert "doppler run" in capsys.readouterr().out

def test_no_mcp_json_errors(tmp_path):
    assert secrets.run(["use", "infisical", "--path", str(tmp_path)]) == 2


def test_summary_var_mode_all_set(tmp_path, monkeypatch):
    _write_mcp(tmp_path)
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    status, _ = secrets.secrets_summary(tmp_path)
    assert status == "PASS"

def test_summary_var_mode_missing_warns(tmp_path, monkeypatch):
    _write_mcp(tmp_path)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    status, detail = secrets.secrets_summary(tmp_path)
    assert status == "WARN"
    assert "GITHUB_TOKEN" in detail

def test_summary_dotenv_present_but_not_loaded(tmp_path, monkeypatch):
    _write_mcp(tmp_path)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    (tmp_path / ".env").write_text("GITHUB_TOKEN=abc\n")
    status, detail = secrets.secrets_summary(tmp_path)
    assert status == "WARN"
    assert "not loaded" in detail.lower()

def test_summary_wrapped_mode_reports_provider(tmp_path, monkeypatch):
    _write_mcp(tmp_path)
    secrets.run(["use", "infisical", "--path", str(tmp_path)])
    monkeypatch.setattr(secrets.shutil, "which", lambda c: "/usr/bin/infisical")
    (tmp_path / ".infisical.json").write_text("{}")
    status, detail = secrets.secrets_summary(tmp_path)
    assert status == "PASS"
    assert "infisical" in detail

def test_parse_env_file_ignores_comments(tmp_path):
    (tmp_path / ".env").write_text("# c\n\nA=1\nB = two \n")
    assert secrets._parse_env_file(tmp_path / ".env") == {"A": "1", "B": "two"}

def test_status_command_runs(tmp_path, capsys):
    _write_mcp(tmp_path)
    assert secrets.run(["status", "--path", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "[PASS]" in out or "[WARN]" in out
