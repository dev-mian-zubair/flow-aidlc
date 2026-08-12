from pathlib import Path

_ENG = Path(__file__).resolve().parents[1] / "src/flow_aidlc/engine"


def test_flow_discover_command_exists():
    cmd = _ENG / "claude/commands/flow-discover.md"
    assert cmd.exists()
    t = cmd.read_text(encoding="utf-8")
    assert "product-intake" in t
    assert "product-roadmap" in t


def test_playbook_has_discover_phase():
    pb = (_ENG / "flow/playbook.md").read_text(encoding="utf-8")
    assert "Discover phase" in pb
    assert "/flow-discover" in pb
    for stage in ["intake", "vision", "pr-faq", "research", "prd", "roadmap"]:
        assert f"steps/discover/{stage}.md" in pb, stage
