"""Tests for `flow ci init` — CI workflow scaffolding."""
from pathlib import Path

from flow_aidlc.commands import ci


def _flow_repo(root: Path, base: str = "main", build: str = "") -> Path:
    """Minimal .flow/config.yaml with vcs.base + graph.build."""
    flow = root / ".flow"
    flow.mkdir(parents=True, exist_ok=True)
    graph = f"graph:\n  build: {build}\n" if build else ""
    (flow / "config.yaml").write_text(f"vcs:\n  base: {base}\n{graph}", encoding="utf-8")
    return root


def test_github_init_writes_workflow(tmp_path):
    _flow_repo(tmp_path, base="main")
    assert ci.run(["init", "--path", str(tmp_path)]) == 0
    wf = tmp_path / ".github" / "workflows" / "flow-check.yml"
    assert wf.exists()
    text = wf.read_text()
    assert "flow check" in text
    assert "branches: [main]" in text


def test_base_branch_stripped_of_remote(tmp_path):
    _flow_repo(tmp_path, base="origin/develop")
    ci.run(["init", "--path", str(tmp_path)])
    text = (tmp_path / ".github" / "workflows" / "flow-check.yml").read_text()
    assert "branches: [develop]" in text          # remote stripped
    assert "origin/develop" not in text


def test_graph_build_step_included_when_configured(tmp_path):
    _flow_repo(tmp_path, build="graphify extract . --code-only")
    ci.run(["init", "--path", str(tmp_path)])
    text = (tmp_path / ".github" / "workflows" / "flow-check.yml").read_text()
    assert "graphify extract . --code-only" in text
    assert "Build code graph" in text


def test_graph_step_absent_when_no_build(tmp_path):
    _flow_repo(tmp_path, build="")
    ci.run(["init", "--path", str(tmp_path)])
    text = (tmp_path / ".github" / "workflows" / "flow-check.yml").read_text()
    assert "Build code graph" not in text


def test_gitlab_provider(tmp_path):
    _flow_repo(tmp_path)
    assert ci.run(["init", "--provider", "gitlab", "--path", str(tmp_path)]) == 0
    gl = tmp_path / ".gitlab-ci.yml"
    assert gl.exists()
    assert "flow check" in gl.read_text()


def test_refuses_overwrite_without_force(tmp_path):
    _flow_repo(tmp_path)
    assert ci.run(["init", "--path", str(tmp_path)]) == 0
    assert ci.run(["init", "--path", str(tmp_path)]) == 1   # exists → refuse


def test_force_overwrites(tmp_path):
    _flow_repo(tmp_path)
    ci.run(["init", "--path", str(tmp_path)])
    assert ci.run(["init", "--force", "--path", str(tmp_path)]) == 0


def test_dry_run_writes_nothing(tmp_path):
    _flow_repo(tmp_path)
    assert ci.run(["init", "--dry-run", "--path", str(tmp_path)]) == 0
    assert not (tmp_path / ".github").exists()


def test_gates_add_semgrep_and_conftest_steps(tmp_path):
    _flow_repo(tmp_path)
    ci.run(["init", "--gates", "semgrep,conftest", "--path", str(tmp_path)])
    text = (tmp_path / ".github" / "workflows" / "flow-check.yml").read_text()
    assert "semgrep scan" in text
    assert "conftest test" in text


def test_no_gates_by_default(tmp_path):
    _flow_repo(tmp_path)
    ci.run(["init", "--path", str(tmp_path)])
    text = (tmp_path / ".github" / "workflows" / "flow-check.yml").read_text()
    assert "semgrep" not in text
    assert "conftest" not in text


def test_unknown_gate_errors(tmp_path):
    _flow_repo(tmp_path)
    assert ci.run(["init", "--gates", "bandit", "--path", str(tmp_path)]) == 2


def test_gates_in_gitlab(tmp_path):
    _flow_repo(tmp_path)
    ci.run(["init", "--provider", "gitlab", "--gates", "semgrep", "--path", str(tmp_path)])
    assert "semgrep scan" in (tmp_path / ".gitlab-ci.yml").read_text()


def test_gates_impeccable_step(tmp_path):
    _flow_repo(tmp_path)
    ci.run(["init", "--gates", "impeccable", "--path", str(tmp_path)])
    text = (tmp_path / ".github" / "workflows" / "flow-check.yml").read_text()
    assert "impeccable detect" in text


def test_gates_impeccable_gitlab(tmp_path):
    _flow_repo(tmp_path)
    ci.run(["init", "--provider", "gitlab", "--gates", "impeccable", "--path", str(tmp_path)])
    assert "impeccable detect" in (tmp_path / ".gitlab-ci.yml").read_text()


def test_registered_in_cli():
    from flow_aidlc.cli import _COMMANDS
    assert "ci" in _COMMANDS
