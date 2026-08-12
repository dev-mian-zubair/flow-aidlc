from pathlib import Path

_A = Path(__file__).resolve().parents[1] / "src/flow_aidlc/engine/claude/agents/product"
_NAMES = ["product-intake", "product-vision", "product-prfaq", "product-research", "product-prd", "product-roadmap"]


def test_all_six_agents_exist():
    for n in _NAMES:
        assert (_A / f"{n}.md").exists(), n


def test_all_agents_inherit_model():
    for n in _NAMES:
        assert "model: inherit" in (_A / f"{n}.md").read_text(encoding="utf-8"), n


_MAY_ORCHESTRATE = {"product-prd", "product-research"}


def test_only_orchestrators_hold_the_agent_tool():
    # product-prd/product-research dispatch the critique panel (Plan 2); the rest stay leaf.
    for n in _NAMES + ["product-critic"]:
        fm = (_A / f"{n}.md").read_text(encoding="utf-8").split("---")[1]
        has_agent = "Agent" in fm
        if n in _MAY_ORCHESTRATE:
            assert has_agent, f"{n} should carry Agent for the panel"
        else:
            assert not has_agent, f"{n} must stay leaf"


def test_research_agent_has_web_and_deep_research():
    t = (_A / "product-research.md").read_text(encoding="utf-8")
    assert "WebSearch" in t and "deep-research" in t


def test_every_agent_has_a_return_contract():
    for n in _NAMES:
        assert "## Return to caller" in (_A / f"{n}.md").read_text(encoding="utf-8"), n
