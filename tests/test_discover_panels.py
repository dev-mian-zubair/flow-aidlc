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
