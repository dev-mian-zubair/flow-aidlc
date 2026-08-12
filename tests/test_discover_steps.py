from pathlib import Path

_STEPS = Path(__file__).resolve().parents[1] / "src/flow_aidlc/engine/flow/steps/discover"


def test_all_six_step_guides_exist():
    for name in ["intake", "vision", "pr-faq", "research", "prd", "roadmap"]:
        assert (_STEPS / f"{name}.md").exists(), name


def test_gated_stages_have_a_checkpoint():
    for name in ["vision", "pr-faq", "research", "prd", "roadmap"]:
        assert "CHECKPOINT" in (_STEPS / f"{name}.md").read_text(encoding="utf-8"), name


def test_research_guide_invokes_deep_research():
    assert "deep-research" in (_STEPS / "research.md").read_text(encoding="utf-8")
