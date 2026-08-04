"""Tests for the M4 authoring-helper commands: guardrail add, map add, doctor.

Each test scaffolds a real Flow instance via `flow init` into a git-init'd
tmp dir, then exercises the command against it with the `--path` flag (which
these commands accept for testability; default is cwd).
"""
import subprocess
from pathlib import Path

import yaml

from flow_aidlc.checks import gate
from flow_aidlc.commands import doctor, guardrail, init, map as map_cmd


def _init_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    rc = init.run(
        ["--yes", "--repo", "acme/app", "--id-prefix", "PI", "--path", str(tmp_path)]
    )
    assert rc == 0
    return tmp_path


def test_guardrail_add_registers_and_gate_passes(tmp_path):
    repo = _init_repo(tmp_path)

    rc = guardrail.run(["add", "budget-integrity", "--prefix", "BUD", "--path", str(repo)])
    assert rc == 0

    md = repo / ".flow" / "guardrails" / "always-on" / "budget-integrity.md"
    assert md.exists()
    text = md.read_text(encoding="utf-8")
    assert "BUD-01" in text
    assert "## Rule" in text
    assert "## Verification" in text

    config = repo / ".flow" / "config.yaml"
    data = yaml.safe_load(config.read_text(encoding="utf-8"))
    assert "budget-integrity" in data["guardrails"]["always_on"]
    # Comments must survive the targeted edit.
    assert "#" in config.read_text(encoding="utf-8")

    tmpl = (repo / ".flow" / "templates" / "requirements.tmpl.md").read_text(encoding="utf-8")
    assert "budget-integrity (see `guardrails/always-on/budget-integrity.md`)" in tmpl

    assert gate.run(repo) == 0


def test_guardrail_add_derives_prefix(tmp_path):
    repo = _init_repo(tmp_path)
    assert guardrail.run(["add", "license-sku-gating", "--path", str(repo)]) == 0
    md = repo / ".flow" / "guardrails" / "always-on" / "license-sku-gating.md"
    assert "LIC-01" in md.read_text(encoding="utf-8")


def test_guardrail_add_optional_not_in_checklist(tmp_path):
    repo = _init_repo(tmp_path)
    assert guardrail.run(["add", "my-optional", "--optional", "--path", str(repo)]) == 0
    md = repo / ".flow" / "guardrails" / "optional" / "my-optional.md"
    assert md.exists()
    data = yaml.safe_load((repo / ".flow" / "config.yaml").read_text(encoding="utf-8"))
    assert "my-optional" in data["guardrails"]["optional"]
    tmpl = (repo / ".flow" / "templates" / "requirements.tmpl.md").read_text(encoding="utf-8")
    assert "my-optional" not in tmpl
    assert gate.run(repo) == 0


def test_guardrail_add_refuses_duplicate(tmp_path):
    repo = _init_repo(tmp_path)
    assert guardrail.run(["add", "budget-integrity", "--path", str(repo)]) == 0
    assert guardrail.run(["add", "budget-integrity", "--path", str(repo)]) == 1


def test_map_add_registers_and_gate_passes(tmp_path):
    repo = _init_repo(tmp_path)

    rc = map_cmd.run(["add", "backend/**", "backend-core", "--path", str(repo)])
    assert rc == 0

    doc = repo / "knowledge" / "map" / "backend-core.md"
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    assert "status: FRESH" in text
    assert "derives-from: [backend/**]" in text

    map_file = repo / ".flow" / "knowledge-map.yaml"
    data = yaml.safe_load(map_file.read_text(encoding="utf-8"))
    docs = [e["doc"] for e in data["maps"]]
    assert "knowledge/map/backend-core.md" in docs

    assert gate.run(repo) == 0


def test_map_add_refuses_duplicate(tmp_path):
    repo = _init_repo(tmp_path)
    assert map_cmd.run(["add", "backend/**", "backend-core", "--path", str(repo)]) == 0
    assert map_cmd.run(["add", "backend/**", "backend-core", "--path", str(repo)]) == 1


def test_map_add_second_entry_preserves_first(tmp_path):
    repo = _init_repo(tmp_path)
    assert map_cmd.run(["add", "backend/**", "backend-core", "--path", str(repo)]) == 0
    assert map_cmd.run(["add", "frontend/**", "frontend-core", "--path", str(repo)]) == 0
    data = yaml.safe_load((repo / ".flow" / "knowledge-map.yaml").read_text(encoding="utf-8"))
    docs = {e["doc"] for e in data["maps"]}
    assert docs == {"knowledge/map/backend-core.md", "knowledge/map/frontend-core.md"}


def test_doctor_ok_on_fresh_init(tmp_path):
    repo = _init_repo(tmp_path)
    assert doctor.run(["--path", str(repo)]) == 0


def test_doctor_not_a_flow_repo(tmp_path):
    # A bare dir with no .flow/ anywhere above → return 2.
    assert doctor.run(["--path", str(tmp_path)]) == 2
