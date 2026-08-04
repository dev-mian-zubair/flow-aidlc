"""Tests for flow_aidlc.checks.freshness — TDD (test written before implementation)."""
import subprocess
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def _setup_repo(tmp_path: Path) -> Path:
    """Initialise a throwaway git repo with a src file and a knowledge doc."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init"], repo)
    _git(["config", "user.email", "test@example.com"], repo)
    _git(["config", "user.name", "Test"], repo)

    # Initial source file
    src = repo / "src"
    src.mkdir()
    (src / "x.py").write_text("# initial\n")

    # Dummy knowledge doc (no frontmatter yet)
    (repo / "doc.md").write_text("---\nverified-at-sha: PLACEHOLDER\n---\n# Doc\n")

    _git(["add", "."], repo)
    _git(["commit", "-m", "initial"], repo)
    return repo


def _get_head(repo: Path) -> str:
    r = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo, capture_output=True, text=True, check=True,
    )
    return r.stdout.strip()


def _write_knowledge_map(repo: Path, sha: str) -> None:
    flow_dir = repo / ".flow"
    flow_dir.mkdir(exist_ok=True)
    (flow_dir / "knowledge-map.yaml").write_text(
        f"maps:\n"
        f"  - doc: doc.md\n"
        f"    derives-from:\n"
        f"      - src/**\n"
    )
    # Stamp the doc with the sha
    (repo / "doc.md").write_text(
        f"---\nverified-at-sha: {sha}\n---\n# Doc\n"
    )


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_fresh_doc_returns_empty(tmp_path):
    """When no commits touch src/** after verified-at-sha, check() returns []."""
    repo = _setup_repo(tmp_path)
    sha = _get_head(repo)
    _write_knowledge_map(repo, sha)
    # commit the knowledge map + stamped doc so they are tracked
    _git(["add", "."], repo)
    _git(["commit", "-m", "stamp knowledge-map"], repo)

    from flow_aidlc.checks.freshness import check
    stale = check(repo)
    assert stale == [], f"Expected no stale docs, got: {stale}"


def test_stale_doc_returned_after_src_change(tmp_path):
    """After a commit touches src/x.py, doc.md should be in the stale list."""
    repo = _setup_repo(tmp_path)
    sha = _get_head(repo)
    _write_knowledge_map(repo, sha)
    _git(["add", "."], repo)
    _git(["commit", "-m", "stamp knowledge-map"], repo)

    # Now touch src/x.py — after the verified-at-sha
    (repo / "src" / "x.py").write_text("# changed\n")
    _git(["add", "."], repo)
    _git(["commit", "-m", "change src/x.py"], repo)

    from flow_aidlc.checks.freshness import check
    stale = check(repo)
    assert "doc.md" in stale, f"Expected doc.md to be stale, got: {stale}"


def test_missing_verified_at_sha_marks_stale(tmp_path):
    """A doc without a verified-at-sha frontmatter key is treated as stale."""
    repo = _setup_repo(tmp_path)
    # knowledge map with no sha in doc.md
    flow_dir = repo / ".flow"
    flow_dir.mkdir(exist_ok=True)
    (flow_dir / "knowledge-map.yaml").write_text(
        "maps:\n  - doc: doc.md\n    derives-from:\n      - src/**\n"
    )
    (repo / "doc.md").write_text("# Doc with no frontmatter\n")
    _git(["add", "."], repo)
    _git(["commit", "-m", "no-sha doc"], repo)

    from flow_aidlc.checks.freshness import check
    stale = check(repo)
    assert "doc.md" in stale, f"Expected doc.md stale (no sha), got: {stale}"
