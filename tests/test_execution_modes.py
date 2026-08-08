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
