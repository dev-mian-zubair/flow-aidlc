"""Tests for flow_aidlc.checks.structure_check — TDD."""
import textwrap
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_flow_dir(tmp_path: Path) -> Path:
    flow = tmp_path / ".flow"
    flow.mkdir()
    # Minimal playbook with no steps references initially
    (flow / "playbook.md").write_text("# Playbook\nNo steps.\n")
    # Minimal config
    (flow / "config.yaml").write_text(
        "version: 0.1.0\n"
        "guardrails:\n"
        "  always_on: []\n"
        "  optional: []\n"
    )
    return flow


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_valid_flow_returns_no_errors(tmp_path):
    """A fully-referenced .flow dir returns []."""
    flow = _make_flow_dir(tmp_path)

    # Add a referenced step file
    steps = flow / "steps" / "scope"
    steps.mkdir(parents=True)
    (steps / "clarify.md").write_text("# Clarify\n")

    # Reference it from playbook
    (flow / "playbook.md").write_text(
        "| Scope | clarify | ALWAYS | `steps/scope/clarify.md` | — | no |\n"
    )

    from flow_aidlc.checks.structure_check import check
    errors = check(flow)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_missing_step_file_is_an_error(tmp_path):
    """A playbook referencing a non-existent step file returns an error."""
    flow = _make_flow_dir(tmp_path)
    (flow / "playbook.md").write_text(
        "| Build | generate | ALWAYS | `steps/build/generate.md` | — | no |\n"
    )
    # steps/build/generate.md does NOT exist

    from flow_aidlc.checks.structure_check import check
    errors = check(flow)
    assert errors, f"Expected at least one error"
    assert any("generate.md" in e or "steps/build/generate.md" in e for e in errors), \
        f"Expected error mentioning generate.md, got: {errors}"


def test_missing_guardrail_file_is_an_error(tmp_path):
    """A config.yaml referencing a guardrail with no .md file returns an error."""
    flow = _make_flow_dir(tmp_path)
    (flow / "config.yaml").write_text(
        "version: 0.1.0\n"
        "guardrails:\n"
        "  always_on: [nonexistent-guardrail]\n"
        "  optional: []\n"
    )
    # No guardrails/always-on/nonexistent-guardrail.md

    from flow_aidlc.checks.structure_check import check
    errors = check(flow)
    assert errors, f"Expected at least one error"
    assert any("nonexistent-guardrail" in e for e in errors), \
        f"Expected error mentioning nonexistent-guardrail, got: {errors}"


def test_config_yaml_missing_is_an_error(tmp_path):
    """A .flow dir without config.yaml returns an error."""
    flow = _make_flow_dir(tmp_path)
    (flow / "config.yaml").unlink()

    from flow_aidlc.checks.structure_check import check
    errors = check(flow)
    assert errors, f"Expected config.yaml missing error"
    assert any("config.yaml" in e for e in errors), \
        f"Expected 'config.yaml' in error, got: {errors}"
