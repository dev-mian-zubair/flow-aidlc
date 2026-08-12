from pathlib import Path

_TPL = Path(__file__).resolve().parents[1] / "src/flow_aidlc/engine/flow/templates/product"


def test_all_six_templates_exist():
    for name in ["progress", "vision", "pr-faq", "research", "prd", "roadmap"]:
        assert (_TPL / f"{name}.tmpl.md").exists(), name


def test_prd_and_roadmap_have_mermaid():
    assert "```mermaid" in (_TPL / "prd.tmpl.md").read_text(encoding="utf-8")
    assert "```mermaid" in (_TPL / "roadmap.tmpl.md").read_text(encoding="utf-8")


def test_research_has_sources_section():
    assert "## Sources" in (_TPL / "research.tmpl.md").read_text(encoding="utf-8")
