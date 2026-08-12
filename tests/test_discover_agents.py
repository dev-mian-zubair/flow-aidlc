from pathlib import Path

_A = Path(__file__).resolve().parents[1] / "src/flow_aidlc/engine/claude/agents/product"
_NAMES = ["product-intake", "product-outcome", "product-prfaq", "product-research", "product-prd", "product-roadmap"]


def test_all_six_agents_exist():
    for n in _NAMES:
        assert (_A / f"{n}.md").exists(), n


def test_all_agents_inherit_model():
    for n in _NAMES:
        assert "model: inherit" in (_A / f"{n}.md").read_text(encoding="utf-8"), n


def test_no_agent_holds_the_agent_tool():
    # leaf agents this iteration — none may carry the Agent/Task tool
    for n in _NAMES:
        fm = (_A / f"{n}.md").read_text(encoding="utf-8").split("---")[1]
        assert "Agent" not in fm and "Task" not in fm, n


def test_research_agent_has_web_and_deep_research():
    t = (_A / "product-research.md").read_text(encoding="utf-8")
    assert "WebSearch" in t and "deep-research" in t


def test_every_agent_has_a_return_contract():
    for n in _NAMES:
        assert "## Return to caller" in (_A / f"{n}.md").read_text(encoding="utf-8"), n
