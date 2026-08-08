# tests/test_execution_modes.py  (new file)
from flow_aidlc.engine_assets import engine_dir


def _engine():
    return engine_dir()


def test_flow_auto_command_exists_and_loads_loop():
    cmd = (_engine() / "claude" / "commands" / "flow-auto.md").read_text()
    assert "steps/auto/loop.md" in cmd
    # The command must state the two hard preconditions.
    assert "flow ci init" in cmd or "CI" in cmd
    assert "flow-auto" in cmd


def test_auto_loop_guide_covers_pull_park_merge_report():
    loop = (_engine() / "flow" / "steps" / "auto" / "loop.md").read_text()
    for marker in ("flow-auto", ".flow/STOP", "max_tasks", "flow-blocked", "green"):
        assert marker in loop, marker


def test_playbook_has_execution_modes_section():
    pb = (_engine() / "flow" / "playbook.md").read_text()
    assert "## Execution modes" in pb
    assert "controlled" in pb and "auto" in pb
    # In auto, the human stop is replaced by the panel — both ideas present.
    assert "/flow-approve" in pb and "panel" in pb.lower()


def test_panel_review_guide_is_stage_typed_and_reuses_pr_review_toolkit():
    pr = (_engine() / "flow" / "steps" / "auto" / "panel-review.md").read_text()
    assert "pr-review-toolkit" in pr           # code gates reuse it
    assert "guardrail-verifier" in pr
    assert "checkpoint-reviewer" in pr          # prose gates
    for marker in ("high-severity", "max_rounds", "park"):
        assert marker in pr, marker
