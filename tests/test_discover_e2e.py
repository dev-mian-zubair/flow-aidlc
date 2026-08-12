import subprocess
from flow_aidlc.commands import init
from flow_aidlc.checks import gate


def _scaffold_unit_from_templates(repo):
    tpl = repo / ".flow/templates/product"
    unit = repo / "docs/flow/product/acme"
    unit.mkdir(parents=True)
    for name in ["vision", "pr-faq", "research", "prd", "roadmap"]:
        (unit / f"{name}.md").write_text(
            (tpl / f"{name}.tmpl.md").read_text(encoding="utf-8"), encoding="utf-8")
    (unit / "progress.md").write_text(
        "---\nid: acme\nkind: product\nparent: null\ngrounding: greenfield\n"
        "status: approved\nsupersedes: null\n"
        "links: {vision: vision.md, pr-faq: pr-faq.md, research: research.md, "
        "prd: prd.md, roadmap: roadmap.md}\n---\n"
        "## Stages\n- [x] vision\n- [x] pr-faq\n- [x] research\n- [x] prd\n- [x] roadmap\n",
        encoding="utf-8")
    return unit


def test_shipped_templates_pass_the_gate(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    assert init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)]) == 0
    unit = _scaffold_unit_from_templates(tmp_path)
    # a fully-scaffolded product unit built from the shipped templates must pass flow check
    assert gate.run(tmp_path) == 0
    assert (unit / "prd.md").exists()


def test_gate_fails_on_missing_required_section(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    assert init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)]) == 0
    unit = _scaffold_unit_from_templates(tmp_path)
    # strip a required section from the PRD → gate must fail
    prd = unit / "prd.md"
    prd.write_text(prd.read_text(encoding="utf-8").replace("## Success metrics", "## Metrics"),
                   encoding="utf-8")
    assert gate.run(tmp_path) == 1
