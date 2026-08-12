import subprocess
from pathlib import Path

from flow_aidlc.commands import init

_ENG = Path(__file__).resolve().parents[1] / "src/flow_aidlc/engine"


def test_product_review_config_renders(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    assert init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)]) == 0
    cfg = (tmp_path / ".flow/config.yaml").read_text(encoding="utf-8")
    assert "review:" in cfg and "panel_size:" in cfg and "market-realist" in cfg


def test_panel_review_step_exists():
    t = (_ENG / "flow/steps/discover/panel-review.md").read_text(encoding="utf-8")
    assert "product-critic" in t
    assert "high-severity" in t.lower() or "high severity" in t.lower()


def test_product_critic_is_read_only():
    t = (_ENG / "claude/agents/product/product-critic.md").read_text(encoding="utf-8")
    fm = t.split("---")[1]
    assert "Write" not in fm and "Agent" not in fm and "Task" not in fm
    assert "model: inherit" in t
    assert "## Return to caller" in t


def test_flow_discover_documents_panel_flag():
    cmd = (_ENG / "claude/commands/flow-discover.md").read_text(encoding="utf-8")
    assert "--panel" in cmd
    assert "panel-review.md" in cmd


def test_playbook_notes_critique_panel():
    pb = (_ENG / "flow/playbook.md").read_text(encoding="utf-8")
    assert "product-critic" in pb or "critique panel" in pb.lower()
