"""`flow doctor` — read-only health check of a Flow repo.

Prints a checklist with a PASS/WARN/FAIL marker per item, then an overall
verdict. Returns 0 when nothing FAILs, 1 when any check FAILs. It touches
nothing on disk — it is purely diagnostic.

Usage:
    flow doctor [--path DIR]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from flow_aidlc.checks._root import find_repo_root
from flow_aidlc.checks.structure_check import check as structure_check

try:
    import yaml
except ImportError:  # pragma: no cover - pyyaml is a runtime dependency
    yaml = None  # type: ignore[assignment]

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"

_MARK = {PASS: "[PASS]", WARN: "[WARN]", FAIL: "[FAIL]"}

# Expected hook scripts under .claude/hooks/ (matches the shipped engine set).
_EXPECTED_HOOKS = (
    "session-start.sh",
    "prompt-journal.sh",
    "scope-guard.sh",
    "freshness-flag.sh",
    "checkpoint-stop.sh",
    "backprop-guard.sh",
    "precompact-save.sh",
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="flow doctor",
        description="Read-only health check of the current Flow repo.",
    )
    p.add_argument("--path", default=None, help="Directory to search upward from for a .flow/ (default: cwd).")
    return p


class _Report:
    """Accumulates check lines and tracks whether any FAILed."""

    def __init__(self) -> None:
        self.any_fail = False

    def line(self, label: str, status: str, detail: str = "") -> None:
        self.any_fail = self.any_fail or status == FAIL
        suffix = f" — {detail}" if detail else ""
        print(f"{_MARK[status]} {label}{suffix}")


def run(argv: list[str]) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2

    root = find_repo_root(args.path)
    flow_dir = root / ".flow"
    if not flow_dir.is_dir():
        print("not a Flow repo — run `flow init` first")
        return 2

    rep = _Report()
    print(f"flow doctor — {root}")
    print()

    _check_flow_present(rep, root, flow_dir)
    _check_config(rep, flow_dir)
    _check_guardrails(rep, flow_dir)
    _check_hooks(rep, root)
    _check_knowledge(rep, root, flow_dir)
    _check_git(rep, root)
    _check_mcp(rep, root)

    print()
    if rep.any_fail:
        print("Verdict: FAIL — fix the [FAIL] items above.")
    else:
        print("Verdict: OK")
    print("Run `flow check` for the full quality gate.")
    return 1 if rep.any_fail else 0


# ---------------------------------------------------------------------------
# individual checks
# ---------------------------------------------------------------------------

def _check_flow_present(rep: _Report, root: Path, flow_dir: Path) -> None:
    missing = [
        rel
        for rel, path in (
            (".flow/", flow_dir),
            (".flow/playbook.md", flow_dir / "playbook.md"),
            (".flow/config.yaml", flow_dir / "config.yaml"),
        )
        if not path.exists()
    ]
    if missing:
        rep.line("Flow present", FAIL, f"missing {', '.join(missing)} — run `flow init`")
    else:
        rep.line("Flow present", PASS, ".flow/ + playbook.md + config.yaml")


def _check_config(rep: _Report, flow_dir: Path) -> None:
    errors = structure_check(flow_dir)
    if errors:
        rep.line("config valid", FAIL, "; ".join(errors))
    else:
        rep.line("config valid", PASS, "config parses; guardrail names resolve to files")


def _check_guardrails(rep: _Report, flow_dir: Path) -> None:
    always_on, optional = _guardrail_lists(flow_dir)
    detail = f"{len(always_on)} always-on, {len(optional)} optional"
    if not always_on:
        rep.line("guardrails", WARN, "no invariants authored yet — `flow guardrail add`")
    else:
        rep.line("guardrails", PASS, detail)


def _check_hooks(rep: _Report, root: Path) -> None:
    hooks_dir = root / ".claude" / "hooks"
    if not hooks_dir.is_dir():
        rep.line("hooks", FAIL, "no .claude/hooks/ directory")
        return

    problems: list[str] = []
    for hook in _EXPECTED_HOOKS:
        path = hooks_dir / hook
        if not path.exists():
            problems.append(f"missing {hook}")
        elif not os.access(path, os.X_OK):
            problems.append(f"{hook} not executable")

    # Cross-check hooks referenced by settings.json actually exist + are runnable.
    settings_path = root / ".claude" / "settings.json"
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            problems.append("settings.json is not valid JSON")
            settings = {}
        for cmd in _referenced_hook_commands(settings):
            referenced = (root / cmd).resolve()
            if not referenced.exists():
                problems.append(f"settings.json references missing {cmd}")
            elif not os.access(referenced, os.X_OK):
                problems.append(f"settings.json references non-executable {cmd}")
    else:
        problems.append("no .claude/settings.json")

    if problems:
        rep.line("hooks", FAIL, "; ".join(problems))
    else:
        rep.line("hooks", PASS, f"{len(_EXPECTED_HOOKS)} hooks present, executable, wired in settings.json")


def _check_knowledge(rep: _Report, root: Path, flow_dir: Path) -> None:
    map_file = flow_dir / "knowledge-map.yaml"
    if not map_file.exists():
        rep.line("knowledge", WARN, "no .flow/knowledge-map.yaml")
        return
    if yaml is None:
        rep.line("knowledge", WARN, "pyyaml not installed — cannot parse knowledge-map.yaml")
        return
    try:
        data = yaml.safe_load(map_file.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        rep.line("knowledge", FAIL, f"knowledge-map.yaml parse error — {exc}")
        return

    maps = data.get("maps", []) or []
    missing_docs = [
        entry.get("doc", "")
        for entry in maps
        if entry.get("doc") and not (root / entry["doc"]).exists()
    ]
    if missing_docs:
        rep.line("knowledge", FAIL, f"map docs not found: {', '.join(missing_docs)}")
        return

    # Freshness is advisory (WARN), never a hard fail here.
    try:
        from flow_aidlc.checks.freshness import check as freshness_check

        stale = freshness_check(root)
    except Exception as exc:  # pragma: no cover - defensive
        rep.line("knowledge", WARN, f"{len(maps)} maps; freshness check errored — {exc}")
        return

    if stale:
        rep.line("knowledge", WARN, f"{len(maps)} maps; {len(stale)} stale — `flow refresh`")
    else:
        rep.line("knowledge", PASS, f"{len(maps)} maps, all docs present and fresh")


def _check_git(rep: _Report, root: Path) -> None:
    if (root / ".git").exists():
        rep.line("git", PASS, ".git present")
    else:
        rep.line("git", WARN, "no .git — Flow's hooks and freshness checks need git")


def _check_mcp(rep: _Report, root: Path) -> None:
    mcp_path = root / ".mcp.json"
    if not mcp_path.exists():
        rep.line("mcp", WARN, "no .mcp.json")
        return
    try:
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        rep.line("mcp", FAIL, f".mcp.json parse error — {exc}")
        return
    servers = [name for name in (data.get("mcpServers", {}) or {}) if not name.startswith("_")]
    if servers:
        rep.line("mcp", PASS, f"servers: {', '.join(sorted(servers))}")
    else:
        rep.line("mcp", WARN, ".mcp.json has no configured servers")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _guardrail_lists(flow_dir: Path) -> tuple[list[str], list[str]]:
    config_path = flow_dir / "config.yaml"
    if yaml is None or not config_path.exists():
        return [], []
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return [], []
    guardrails = data.get("guardrails", {}) or {}
    always_on = [str(v) for v in (guardrails.get("always_on", []) or [])]
    optional = [str(v) for v in (guardrails.get("optional", []) or [])]
    return always_on, optional


def _referenced_hook_commands(settings: dict) -> list[str]:
    """Extract every hook `command` path referenced in a settings.json dict."""
    commands: list[str] = []
    for groups in (settings.get("hooks", {}) or {}).values():
        for group in groups or []:
            for hook in group.get("hooks", []) or []:
                cmd = hook.get("command")
                # Only cross-check local hook script paths under .claude/hooks/.
                if cmd and cmd.startswith(".claude/hooks/"):
                    commands.append(cmd)
    return commands
