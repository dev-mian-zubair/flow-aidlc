"""Regression tests for the instruction-audit critical path bugs.

These lock the two silent path-prefix defects the audit found:
  - hooks resolved the worklog/knowledge dirs at the wrong root (`$root/worklog`
    instead of `$root/docs/flow/worklog`), silently no-opping every governance hook;
  - Discover step guides read templates from a bare `templates/product/` path
    instead of `.flow/templates/product/`, breaking scaffolding Reads.

They are grep-level checks on the shipped engine assets — cheap, and they fail
loudly if the prefixes ever regress.
"""
import re
from pathlib import Path

_ENG = Path(__file__).resolve().parents[1] / "src/flow_aidlc/engine"
_HOOKS = _ENG / "claude/hooks"
_A = _ENG / "claude/agents"


def test_hook_lib_resolves_canonical_worklog_path():
    t = (_HOOKS / "_lib.sh").read_text(encoding="utf-8")
    assert "docs/flow/worklog" in t
    # the bug: a bare `$root/worklog` (missing the docs/flow/ prefix)
    assert not re.search(r"\$root/worklog\b", t), "hook must resolve $root/docs/flow/worklog"


def test_session_start_resolves_canonical_knowledge_path():
    t = (_HOOKS / "session-start.sh").read_text(encoding="utf-8")
    assert "docs/flow/knowledge/map" in t
    assert not re.search(r"\$root/knowledge\b", t), "hook must resolve $root/docs/flow/knowledge/map"


def test_hook_commands_use_project_dir_prefix():
    import json
    settings = json.loads((_ENG / "claude/settings.json").read_text(encoding="utf-8"))
    cmds = [
        h["command"]
        for group in settings["hooks"].values()
        for matcher in group
        for h in matcher["hooks"]
    ]
    assert cmds, "no hook commands found"
    for c in cmds:
        assert c.startswith("${CLAUDE_PROJECT_DIR}/"), f"hook command not project-dir-anchored: {c}"


def test_plugin_hook_commands_use_plugin_root_only():
    """The generated plugin manifest must anchor hooks at ${CLAUDE_PLUGIN_ROOT}
    and never carry a stacked ${CLAUDE_PROJECT_DIR}/${CLAUDE_PLUGIN_ROOT} prefix."""
    import json
    plugin_hooks = Path(__file__).resolve().parents[1] / "plugin/hooks/hooks.json"
    if not plugin_hooks.exists():
        return  # plugin not built in this checkout — engine tests still cover the source
    data = json.loads(plugin_hooks.read_text(encoding="utf-8"))
    cmds = [
        h["command"]
        for group in data["hooks"].values()
        for matcher in group
        for h in matcher["hooks"]
    ]
    assert cmds, "no plugin hook commands found"
    for c in cmds:
        assert c.startswith("${CLAUDE_PLUGIN_ROOT}/hooks/"), f"plugin hook not plugin-root-anchored: {c}"
        assert "CLAUDE_PROJECT_DIR" not in c, f"plugin hook carries a stacked project-dir prefix: {c}"


def _no_bare_product_template_ref(text: str) -> bool:
    # every `templates/product/` occurrence must be part of `.flow/templates/product/`
    return text.count("templates/product/") == text.count(".flow/templates/product/")


def test_discover_steps_reference_flow_prefixed_templates():
    for name in ["intake", "vision", "pr-faq", "research", "prd", "roadmap"]:
        t = (_ENG / f"flow/steps/discover/{name}.md").read_text(encoding="utf-8")
        assert _no_bare_product_template_ref(t), f"discover/{name}.md has a bare templates/product/ ref"


def test_product_intake_references_flow_prefixed_templates():
    t = (_A / "product/product-intake.md").read_text(encoding="utf-8")
    assert _no_bare_product_template_ref(t)
