"""Tests for flow_aidlc.checks.guardrail_lint — written before implementation (TDD)."""
import re
import textwrap
from pathlib import Path

import pytest


# ---- fixtures ----

@pytest.fixture()
def guardrails_dir(tmp_path):
    """A guardrail directory with valid guardrails in subdirectories (matching real layout)."""
    root = tmp_path / "guardrails"
    # always-on/ subdir
    always_on = root / "always-on"
    always_on.mkdir(parents=True)
    (always_on / "migration-safety.md").write_text(textwrap.dedent("""\
        # Migration Safety
        **ID prefix:** MIG

        ## Rule
        Always migrate safely.

        ## Verification
        - **MIG-01** check one
        - **MIG-02** check two
    """))
    # optional/ subdir
    optional = root / "optional"
    optional.mkdir(parents=True)
    (optional / "code-style.md").write_text(textwrap.dedent("""\
        # Code Style
        **ID prefix:** STY

        ## Rule
        Follow the style guide.

        ## Verification
        - **STY-01** lint passes
    """))
    return root


# ---- tests ----

def test_valid_guardrail_returns_no_errors(guardrails_dir):
    """A well-formed guardrail dir returns an empty error list."""
    from flow_aidlc.checks.guardrail_lint import lint
    errors = lint(guardrails_dir)
    assert errors == [], f"Expected no errors but got: {errors}"


def test_missing_verification_section_is_an_error(guardrails_dir):
    """A guardrail missing ## Verification returns an error referencing that file."""
    (guardrails_dir / "always-on" / "broken.md").write_text(textwrap.dedent("""\
        # Broken
        ## Rule
        Some rule.
    """))
    from flow_aidlc.checks.guardrail_lint import lint
    errors = lint(guardrails_dir)
    broken_errors = [e for e in errors if "broken.md" in e]
    assert broken_errors, f"Expected an error for broken.md, got: {errors}"
    assert any("Verification" in e for e in broken_errors), \
        f"Expected 'Verification' in error, got: {broken_errors}"


def test_missing_rule_section_is_an_error(guardrails_dir):
    """A guardrail with ## Verification but missing ## Rule returns an error mentioning Rule."""
    (guardrails_dir / "optional" / "no-rule.md").write_text(textwrap.dedent("""\
        # No Rule
        ## Verification
        - **NR-01** some check
    """))
    from flow_aidlc.checks.guardrail_lint import lint
    errors = lint(guardrails_dir)
    norule_errors = [e for e in errors if "no-rule.md" in e]
    assert norule_errors, f"Expected an error for no-rule.md, got: {errors}"
    assert any("Rule" in e for e in norule_errors), \
        f"Expected 'Rule' in error message, got: {norule_errors}"


def test_duplicate_id_is_an_error(guardrails_dir):
    """Two guardrails sharing the same bold ID return a duplicate-ID error."""
    (guardrails_dir / "optional" / "other.md").write_text(textwrap.dedent("""\
        # Other
        ## Rule
        Another rule.

        ## Verification
        - **MIG-01** duplicate of migration-safety.md's MIG-01
    """))
    from flow_aidlc.checks.guardrail_lint import lint
    errors = lint(guardrails_dir)
    dup_errors = [e for e in errors if "MIG-01" in e and ("duplicate" in e.lower() or "dup" in e.lower())]
    assert dup_errors, f"Expected duplicate-ID error for MIG-01, got: {errors}"


def test_error_uses_relative_path_not_bare_filename(guardrails_dir):
    """Error messages include the subdir path (e.g. always-on/broken.md), not just filename."""
    (guardrails_dir / "always-on" / "subdir-broken.md").write_text(textwrap.dedent("""\
        # Subdir Broken
        ## Rule
        Some rule.
    """))
    from flow_aidlc.checks.guardrail_lint import lint
    errors = lint(guardrails_dir)
    subdir_errors = [e for e in errors if "subdir-broken.md" in e]
    assert subdir_errors, f"Expected an error for subdir-broken.md, got: {errors}"
    # The path in the error must include the subdirectory component
    assert any(("always-on" in e or "/" in e.split("subdir-broken.md")[0]) for e in subdir_errors), \
        f"Expected relative path (with subdir) in error, got: {subdir_errors}"


def test_ask_md_files_are_excluded(guardrails_dir):
    """*.ask.md files are skipped (they are prompt variants, not guardrail specs)."""
    (guardrails_dir / "always-on" / "test-coverage.ask.md").write_text(
        "# Ask variant\nNo Rule section.\n"
    )
    from flow_aidlc.checks.guardrail_lint import lint
    errors = lint(guardrails_dir)
    ask_errors = [e for e in errors if "ask.md" in e]
    assert ask_errors == [], f"Expected .ask.md to be skipped, got: {ask_errors}"


def test_nested_guardrails_are_linted(guardrails_dir):
    """Files in subdirectories (always-on/, optional/) are all linted."""
    # Add a broken file in a subdir to confirm nested linting works
    (guardrails_dir / "optional" / "nested-broken.md").write_text(textwrap.dedent("""\
        # Nested Broken
        ## Verification
        - **NB-01** some check
    """))
    from flow_aidlc.checks.guardrail_lint import lint
    errors = lint(guardrails_dir)
    nested_errors = [e for e in errors if "nested-broken.md" in e]
    assert nested_errors, f"Expected an error for nested file, got: {errors}"
    # Error path must reflect nested location
    assert any("optional" in e for e in nested_errors), \
        f"Expected 'optional/' in error path, got: {nested_errors}"
