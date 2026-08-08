from flow_aidlc.engine_assets import engine_dir


def _e():
    return engine_dir()


def test_generate_guide_mentions_impeccable_ui():
    t = (_e() / "flow" / "steps" / "build" / "generate.md").read_text()
    assert "impeccable" in t.lower() and "DESIGN.md" in t


def test_verify_guide_mentions_impeccable_validation():
    t = (_e() / "flow" / "steps" / "build" / "verify.md").read_text()
    assert "impeccable" in t.lower()


def test_panel_review_adds_impeccable_ui_lens():
    t = (_e() / "flow" / "steps" / "auto" / "panel-review.md").read_text()
    assert "impeccable" in t.lower() and "UI" in t


def test_knowledge_map_references_standards():
    t = (_e() / "flow" / "knowledge-map.tmpl.yaml").read_text()
    assert "PRODUCT.md" in t and "DESIGN.md" in t
