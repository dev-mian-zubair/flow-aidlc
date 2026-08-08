"""Tests for flow_aidlc.checks.config_consistency — the config-vs-prose drift gate."""
import textwrap
from pathlib import Path

from flow_aidlc.checks.config_consistency import check
from flow_aidlc.checks.gate import run as gate_run


# ---------------------------------------------------------------------------
# helper: build a minimal repo that `check()` returns [] on, then perturb it
# ---------------------------------------------------------------------------

def _make_repo(tmp_path: Path) -> Path:
    root = tmp_path
    flow = root / ".flow"
    (flow / "guardrails" / "always-on").mkdir(parents=True)
    (flow / "guardrails" / "optional").mkdir(parents=True)
    (flow / "steps" / "shared").mkdir(parents=True)
    (flow / "steps" / "ship").mkdir(parents=True)
    (flow / "steps" / "build").mkdir(parents=True)
    (root / ".claude" / "agents" / "review").mkdir(parents=True)
    (root / "src").mkdir()  # a graph.focus dir that exists (C7)
    (root / ".graphifyignore").write_text("node_modules/\n")  # graph.ignore_file exists (C7)

    # one always-on guardrail with a valid rule file (also satisfies guardrail_lint)
    (flow / "guardrails" / "always-on" / "g1.md").write_text(
        "# G1\n## Rule\nx\n## Verification\n- **G1-01** x\n"
    )
    # tracker adapter: github mapped, jira a stub
    (flow / "steps" / "shared" / "tracker.md").write_text(
        "# Tracker\n### github\ngithub mapping\n### jira — NOT IMPLEMENTED\nstub\n"
    )
    # graph adapter: graphify mapped, neo4j a stub
    (flow / "steps" / "shared" / "graph.md").write_text(
        "# Graph\n### graphify\ngraphify mapping\n### neo4j — NOT IMPLEMENTED\nstub\n"
    )
    # branch-hardening guide mentions the review agent
    (flow / "steps" / "ship" / "branch-hardening.md").write_text(
        "# BH\n- `pr-review-toolkit:code-reviewer`\n"
    )
    # echo files mention g1 (word-boundary friendly)
    (flow / "playbook.md").write_text("always_on: `g1`\n")
    (flow / "steps" / "build" / "verify.md").write_text("guardrails: `g1`\n")
    (root / ".claude" / "agents" / "review" / "guardrail-verifier.md").write_text(
        "enforces `g1`\n"
    )
    (flow / "config.yaml").write_text(textwrap.dedent("""\
        guardrails:
          always_on: [g1]
          optional: []
        tracker:
          platform: github
          repo: acme/pip
        review:
          branch_hardening:
            - pr-review-toolkit:code-reviewer
        graph:
          backend: graphify
          root: "."
          ignore_file: .graphifyignore
          focus:
            - src
        """))
    return root


# ---------------------------------------------------------------------------
# valid baseline
# ---------------------------------------------------------------------------

def test_valid_repo_returns_no_errors(tmp_path):
    assert check(_make_repo(tmp_path)) == []


# ---------------------------------------------------------------------------
# C1 — guardrail parity
# ---------------------------------------------------------------------------

def test_c1_missing_rule_file(tmp_path):
    root = _make_repo(tmp_path)
    (root / ".flow" / "guardrails" / "always-on" / "g1.md").unlink()
    errs = check(root)
    assert any("C1" in e and "g1" in e and "missing" in e for e in errs), errs


def test_c1_orphan_rule_file(tmp_path):
    root = _make_repo(tmp_path)
    (root / ".flow" / "guardrails" / "always-on" / "g2.md").write_text(
        "## Rule\nx\n## Verification\n- **G2-01** x\n"
    )
    errs = check(root)
    assert any("C1" in e and "g2" in e and "not in config" in e for e in errs), errs


def test_c1_ask_md_is_not_a_rule_file(tmp_path):
    root = _make_repo(tmp_path)
    # an .ask.md opt-in stub must NOT be treated as an orphan rule file
    (root / ".flow" / "guardrails" / "optional" / "sec.ask.md").write_text("prompt\n")
    assert check(root) == []


# ---------------------------------------------------------------------------
# C2 — no hardcoded repo (+ allow marker)
# ---------------------------------------------------------------------------

def test_c2_hardcoded_repo_blocks(tmp_path):
    root = _make_repo(tmp_path)
    (root / ".flow" / "runbook.md").write_text("clone acme/pip please\n")
    errs = check(root)
    assert any("C2" in e and "runbook.md" in e for e in errs), errs


def test_c2_allow_marker_opts_out(tmp_path):
    root = _make_repo(tmp_path)
    (root / ".flow" / "runbook.md").write_text(
        "<!-- config-consistency: allow-repo-literal -->\nclone acme/pip\n"
    )
    assert check(root) == []


# ---------------------------------------------------------------------------
# C3 — tracker platform implemented
# ---------------------------------------------------------------------------

def test_c3_stub_platform_blocks(tmp_path):
    root = _make_repo(tmp_path)
    cfg = (root / ".flow" / "config.yaml").read_text().replace("platform: github", "platform: jira")
    (root / ".flow" / "config.yaml").write_text(cfg)
    errs = check(root)
    assert any("C3" in e and "jira" in e for e in errs), errs


def test_c3_stub_detection_is_case_insensitive(tmp_path):
    root = _make_repo(tmp_path)
    (root / ".flow" / "steps" / "shared" / "tracker.md").write_text(
        "### github\ngithub mapping\n### jira — Not Implemented\nstub\n"
    )
    cfg = (root / ".flow" / "config.yaml").read_text().replace("platform: github", "platform: jira")
    (root / ".flow" / "config.yaml").write_text(cfg)
    errs = check(root)
    assert any("C3" in e and "jira" in e for e in errs), errs


# ---------------------------------------------------------------------------
# C5 — review echo presence
#
# NOTE: this package intentionally de-hardcodes the always_on guardrail list in
# its prose files (guardrail-verifier / playbook / build-verify treat config.yaml
# as the sole source of truth), so the skipped C4 "guardrail echo"
# check does not apply here.
# ---------------------------------------------------------------------------

def test_c5_missing_review_echo_blocks(tmp_path):
    root = _make_repo(tmp_path)
    (root / ".flow" / "steps" / "ship" / "branch-hardening.md").write_text("no agents here\n")
    errs = check(root)
    assert any("C5" in e and "code-reviewer" in e for e in errs), errs


# ---------------------------------------------------------------------------
# C6 — graph backend implemented
# ---------------------------------------------------------------------------

def test_c6_stub_backend_blocks(tmp_path):
    root = _make_repo(tmp_path)
    cfg = (root / ".flow" / "config.yaml").read_text().replace("backend: graphify", "backend: neo4j")
    (root / ".flow" / "config.yaml").write_text(cfg)
    errs = check(root)
    assert any("C6" in e and "neo4j" in e for e in errs), errs


def test_c7_missing_focus_dir_blocks(tmp_path):
    root = _make_repo(tmp_path)
    cfg = (root / ".flow" / "config.yaml").read_text().replace("- src", "- nonexistent-dir")
    (root / ".flow" / "config.yaml").write_text(cfg)
    errs = check(root)
    assert any("C7" in e and "graph.focus" in e and "nonexistent-dir" in e for e in errs), errs


def test_c7_missing_root_blocks(tmp_path):
    root = _make_repo(tmp_path)
    cfg = (root / ".flow" / "config.yaml").read_text().replace('root: "."', 'root: no-such-root')
    (root / ".flow" / "config.yaml").write_text(cfg)
    errs = check(root)
    assert any("C7" in e and "graph.root" in e and "no-such-root" in e for e in errs), errs


def test_c7_missing_ignore_file_blocks(tmp_path):
    root = _make_repo(tmp_path)
    (root / ".graphifyignore").unlink()
    errs = check(root)
    assert any("C7" in e and "graph.ignore_file" in e for e in errs), errs


# ---------------------------------------------------------------------------
# fail-open posture (the whole point of the finding)
# ---------------------------------------------------------------------------

def test_absent_config_is_skipped(tmp_path):
    # no .flow/config.yaml at all → genuinely nothing to enforce → []
    (tmp_path / ".flow").mkdir()
    assert check(tmp_path) == []


def test_malformed_config_blocks_not_failopen(tmp_path):
    root = _make_repo(tmp_path)
    (root / ".flow" / "config.yaml").write_text("guardrails: [unclosed\n:::bad yaml")
    errs = check(root)
    assert errs, "a config that cannot be parsed must NOT silently pass"
    assert any("failed to parse" in e for e in errs), errs


# ---------------------------------------------------------------------------
# gate wiring — a config-consistency violation must fail the composed gate
# ---------------------------------------------------------------------------

def test_gate_clean_repo_passes(tmp_path):
    assert gate_run(_make_repo(tmp_path)) == 0


def test_gate_fails_on_config_consistency_violation(tmp_path):
    root = _make_repo(tmp_path)
    (root / ".flow" / "runbook.md").write_text("clone acme/pip\n")  # C2 violation
    assert gate_run(root) == 1


# ---------------------------------------------------------------------------
# every shipped tracker is implemented end-to-end — each passes C3
# ---------------------------------------------------------------------------

def test_shipped_adapter_implements_all_trackers():
    """The shipped tracker adapter maps github/jira/linear — no NOT IMPLEMENTED heading."""
    import re

    from flow_aidlc.engine_assets import engine_dir

    adapter = (engine_dir() / "flow" / "steps" / "shared" / "tracker.md").read_text()
    # Every platform has a real section heading...
    for platform in ("github", "jira", "linear", "azure-devops", "shortcut", "asana", "clickup"):
        assert f"### {platform}\n" in adapter, platform
    # ...and no platform heading is marked as a NOT IMPLEMENTED stub.
    assert not re.search(r"^### [\w-]+ — NOT IMPLEMENTED", adapter, re.MULTILINE), adapter


def _init_and_check(tmp_path, platform: str, key: str):
    import subprocess

    from flow_aidlc.commands import init

    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    rc = init.run([
        "--yes", "--tracker", platform, "--repo", key, "--id-prefix", key,
        "--path", str(tmp_path),
    ])
    assert rc == 0
    return check(tmp_path)


def test_c3_jira_passes_end_to_end(tmp_path):
    """`flow init --tracker jira` produces an instance the gate accepts."""
    errs = _init_and_check(tmp_path, "jira", "PROJ")
    assert not any("C3" in e for e in errs), errs
    assert errs == [], errs


def test_c3_linear_passes_end_to_end(tmp_path):
    """`flow init --tracker linear` produces an instance the gate accepts."""
    errs = _init_and_check(tmp_path, "linear", "ENG")
    assert not any("C3" in e for e in errs), errs
    assert errs == [], errs


import pytest


@pytest.mark.parametrize(
    "platform,key",
    [
        ("azure-devops", "ADOPRJ"),
        ("shortcut", "SCWORK"),
        ("asana", "ASPROJ"),
        ("clickup", "CULIST"),
    ],
)
def test_c3_new_trackers_pass_end_to_end(tmp_path, platform, key):
    """Each newly-wired tracker produces an instance the gate fully accepts."""
    errs = _init_and_check(tmp_path, platform, key)
    assert not any("C3" in e for e in errs), errs
    assert errs == [], errs
