"""`flow init` — scaffold a Flow instance into a target repo.

Copies the packaged engine (``flow/`` → ``.flow/``, ``claude/`` → ``.claude/``,
``knowledge/`` → ``knowledge/``), renders the three ``.tmpl`` config files with
project-specific token values, merges Claude hook settings into any existing
``settings.json``, and wires up ``.gitignore`` / ``CLAUDE.md`` pointers. Copies
the artifact templates (``flow/templates/*.tmpl.md``) verbatim — those carry
``[Answer]:`` placeholders filled at stage time, not init-time tokens.

Idempotence guard: refuses to run over an existing ``.flow/`` unless ``--force``.
``--dry-run`` prints every planned action and writes nothing.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from flow_aidlc import __version__
from flow_aidlc.engine_assets import TOKEN_DEFAULTS, engine_dir, merge_settings, render

# Files under engine/flow/ that are rendered separately (skip on the verbatim copy).
_FLOW_TMPL_SKIP = {"config.tmpl.yaml", "knowledge-map.tmpl.yaml"}
# Files under engine/claude/ handled specially (rendered / merged), not plain-copied.
_CLAUDE_SPECIAL = {"mcp.tmpl.json", "settings.json"}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="flow init",
        description="Scaffold the Flow instance into a target repo.",
    )
    p.add_argument("--tracker", default="github", help="Tracker platform (default: github).")
    p.add_argument("--repo", default=None, help="Tracker repo as owner/name.")
    p.add_argument("--id-prefix", default="TASK", help="Ticket ID prefix (default: TASK).")
    p.add_argument("--base", default="origin/main", help="Default base branch for feature branches + PR target (default: origin/main).")
    p.add_argument("--test-cmd", default=None, help="Project test command.")
    p.add_argument("--build-cmd", default=None, help="Project build command.")
    p.add_argument("--lint-cmd", default=None, help="Project lint command.")
    p.add_argument("--typecheck-cmd", default=None, help="Project typecheck command.")
    p.add_argument("--db-uri", default=None, help="Read-only DB URI for the postgres MCP.")
    p.add_argument("-y", "--yes", action="store_true", help="Non-interactive: use flags/defaults, no prompts.")
    p.add_argument("--dry-run", action="store_true", help="Print planned actions; write nothing.")
    p.add_argument("--force", action="store_true", help="Overwrite an existing .flow/.")
    p.add_argument("--path", default=None, help="Target directory (default: current directory).")
    return p


# Each token → a human label (for interactive prompts and the summary).
_TOKEN_FLAG_LABEL = {
    "TRACKER_PLATFORM": "Tracker platform",
    "TRACKER_REPO": "Tracker repo (owner/name)",
    "ID_PREFIX": "Ticket ID prefix",
    "BASE_BRANCH": "Default base branch",
    "TEST_CMD": "Test command",
    "BUILD_CMD": "Build command",
    "LINT_CMD": "Lint command",
    "TYPECHECK_CMD": "Typecheck command",
    "FLOW_DB_READONLY_URI": "Read-only DB URI",
}


def _gather_values(args: argparse.Namespace, interactive: bool) -> dict[str, str]:
    """Compose token values: defaults ← flags ← (optionally) interactive prompts."""
    values = dict(TOKEN_DEFAULTS)

    # Flags override defaults.
    if args.tracker:
        values["TRACKER_PLATFORM"] = args.tracker
        values["TRACKER_MCP"] = args.tracker
    if args.repo is not None:
        values["TRACKER_REPO"] = args.repo
    if args.id_prefix:
        values["ID_PREFIX"] = args.id_prefix
    if args.base:
        values["BASE_BRANCH"] = args.base
    if args.test_cmd is not None:
        values["TEST_CMD"] = args.test_cmd
    if args.build_cmd is not None:
        values["BUILD_CMD"] = args.build_cmd
    if args.lint_cmd is not None:
        values["LINT_CMD"] = args.lint_cmd
    if args.typecheck_cmd is not None:
        values["TYPECHECK_CMD"] = args.typecheck_cmd
    if args.db_uri is not None:
        values["FLOW_DB_READONLY_URI"] = args.db_uri

    if interactive:
        for token, label in _TOKEN_FLAG_LABEL.items():
            current = values.get(token, "")
            shown = f" [{current}]" if current else " []"
            resp = input(f"{label}{shown}: ").strip()
            if resp:
                values[token] = resp
        # Keep MCP in lock-step with the platform if it was prompted.
        values["TRACKER_MCP"] = values["TRACKER_PLATFORM"]

    return values


def run(argv: list[str]) -> int:
    args = _build_parser().parse_args(argv)

    target = Path(args.path).resolve() if args.path else Path.cwd().resolve()
    flow_dir = target / ".flow"
    dry = args.dry_run

    # ---- Guards -----------------------------------------------------------
    if flow_dir.exists() and not args.force:
        print("Flow already initialised here (use --force to re-scaffold)")
        return 1

    if not (target / ".git").exists():
        sys.stderr.write(
            f"WARNING: {target} is not a git repo — Flow's hooks and the code "
            "graph work best inside one. Continuing anyway.\n"
        )

    interactive = sys.stdin.isatty() and not args.yes
    values = _gather_values(args, interactive)

    eng = engine_dir()

    def action(msg: str) -> None:
        print(("DRY-RUN: would " if dry else "") + msg)

    # ---- 1. flow/ → .flow/ (skip the two rendered .tmpl configs) ----------
    action(f"copy engine/flow/ -> {flow_dir} (verbatim, minus rendered configs)")
    if not dry:
        _copy_tree(eng / "flow", flow_dir, skip_names=_FLOW_TMPL_SKIP)

    # ---- 2. claude/ → .claude/ (skip mcp.tmpl.json + settings.json) -------
    claude_dir = target / ".claude"
    action(f"copy engine/claude/ -> {claude_dir} (minus mcp.tmpl.json + settings.json)")
    if not dry:
        _copy_tree(eng / "claude", claude_dir, skip_names=_CLAUDE_SPECIAL)
        _chmod_hooks(claude_dir / "hooks")

    # ---- 3. knowledge/ → knowledge/ ---------------------------------------
    know_dir = target / "knowledge"
    action(f"copy engine/knowledge/ -> {know_dir}")
    if not dry:
        _copy_tree(eng / "knowledge", know_dir)

    # ---- 4. render config.tmpl.yaml -> .flow/config.yaml ------------------
    action(f"render config.tmpl.yaml -> {flow_dir / 'config.yaml'}")
    if not dry:
        _render_file(eng / "flow" / "config.tmpl.yaml", flow_dir / "config.yaml", values)

    # ---- 5. render knowledge-map.tmpl.yaml -> .flow/knowledge-map.yaml ----
    action(f"render knowledge-map.tmpl.yaml -> {flow_dir / 'knowledge-map.yaml'}")
    if not dry:
        _render_file(eng / "flow" / "knowledge-map.tmpl.yaml", flow_dir / "knowledge-map.yaml", values)

    # ---- 6. render mcp.tmpl.json -> .mcp.json (repo ROOT) -----------------
    action(f"render mcp.tmpl.json -> {target / '.mcp.json'}")
    if not dry:
        _render_file(eng / "claude" / "mcp.tmpl.json", target / ".mcp.json", values)

    # ---- 7. worklog/ dir --------------------------------------------------
    action(f"ensure {target / 'worklog'} exists")
    if not dry:
        (target / "worklog").mkdir(parents=True, exist_ok=True)

    # ---- settings.json merge ----------------------------------------------
    action(f"merge Claude hooks into {claude_dir / 'settings.json'}")
    if not dry:
        merge_settings(eng / "claude" / "settings.json", claude_dir / "settings.json")

    # ---- .env.example (secret inventory scanned from the rendered .mcp.json) --
    action(f"write {target / '.env.example'} (required credential vars)")
    if not dry:
        _write_env_example(target)

    # ---- .gitignore -------------------------------------------------------
    action("ensure .gitignore covers worklog/.active, .superpowers/, .env, and the graph cache")
    if not dry:
        _ensure_gitignore(
            target / ".gitignore",
            [
                "worklog/.active",
                ".superpowers/",
                ".env",
                # Code graph: only graphify-out/graph.json is committed; ignore the
                # build cache, root marker, and manifest graphify writes beside it.
                "graphify-out/*",
                "!graphify-out/graph.json",
            ],
        )

    # ---- CLAUDE.md pointer ------------------------------------------------
    action(f"ensure {target / 'CLAUDE.md'} points at .flow/playbook.md")
    if not dry:
        _ensure_claude_md(target / "CLAUDE.md")

    # ---- VERSION (the copied .flow/VERSION already carries the engine ver) -
    if not dry:
        version_file = flow_dir / "VERSION"
        if not version_file.exists():
            version_file.write_text(f"{__version__}\n", encoding="utf-8")

    # ---- Summary ----------------------------------------------------------
    _print_summary(target, values, dry)
    return 0


# ---------------------------------------------------------------------------
# filesystem helpers
# ---------------------------------------------------------------------------

def _copy_tree(src: Path, dst: Path, skip_names: set[str] | None = None) -> None:
    """Recursively copy ``src`` into ``dst``, skipping any top-level basename in
    ``skip_names``. Existing files are overwritten; subdirs are preserved."""
    skip_names = skip_names or set()
    dst.mkdir(parents=True, exist_ok=True)
    for item in sorted(src.iterdir()):
        if item.name in skip_names:
            continue
        target = dst / item.name
        if item.is_dir():
            _copy_tree(item, target)
        else:
            shutil.copy2(item, target)


def _chmod_hooks(hooks_dir: Path) -> None:
    """Ensure copied hook scripts stay executable."""
    if not hooks_dir.is_dir():
        return
    for sh in hooks_dir.glob("*.sh"):
        mode = sh.stat().st_mode
        sh.chmod(mode | 0o111)


def _render_file(src: Path, dst: Path, values: dict[str, str]) -> None:
    """Token-render ``src`` and write the result to ``dst``."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(render(src.read_text(encoding="utf-8"), values), encoding="utf-8")


def _write_env_example(target: Path) -> None:
    """Write .env.example listing every ${VAR} referenced in the rendered .mcp.json.

    This is the fallback path for users not using a secrets manager (`flow
    secrets use`). Real .env is gitignored; .env.example is committed.
    """
    from flow_aidlc import mcp_config

    mcp_path = target / ".mcp.json"
    if not mcp_path.exists():
        return
    variables = mcp_config.all_secret_vars(mcp_config.load_mcp(mcp_path))
    header = (
        "# Flow tracker/MCP credentials — copy to .env and fill in.\n"
        "# .env is gitignored. Load it (direnv, or `set -a; source .env; set +a`)\n"
        "# before launching Claude Code — or use `flow secrets use <provider>`.\n\n"
    )
    body = "".join(f"{var}=\n" for var in variables) or "# (no credential vars required)\n"
    (target / ".env.example").write_text(header + body, encoding="utf-8")


def _ensure_gitignore(path: Path, entries: list[str]) -> None:
    """Append any missing ``entries`` to ``.gitignore`` (creating it if absent)."""
    existing_lines: set[str] = set()
    text = ""
    if path.exists():
        text = path.read_text(encoding="utf-8")
        existing_lines = {line.strip() for line in text.splitlines()}

    missing = [e for e in entries if e not in existing_lines]
    if not missing:
        return

    prefix = ""
    if text and not text.endswith("\n"):
        prefix = "\n"
    addition = prefix + "\n".join(missing) + "\n"
    path.write_text(text + addition, encoding="utf-8")


_CLAUDE_MD_SECTION = (
    "## The Flow\n\n"
    "This repo uses Flow — a governed AI-DLC methodology. Start at "
    "`.flow/README.md` then `.flow/playbook.md`. Run `flow check` for the "
    "quality gate.\n"
)


def _ensure_claude_md(path: Path) -> None:
    """Append the Flow pointer section to CLAUDE.md, or create a minimal one."""
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if ".flow/playbook.md" in text:
            return
        prefix = "" if text.endswith("\n") else "\n"
        path.write_text(text + prefix + "\n" + _CLAUDE_MD_SECTION, encoding="utf-8")
    else:
        path.write_text("# CLAUDE.md\n\n" + _CLAUDE_MD_SECTION, encoding="utf-8")


def _print_summary(target: Path, values: dict[str, str], dry: bool) -> None:
    banner = "Flow init (dry-run) — nothing written." if dry else "Flow initialised."
    print()
    print(banner)
    print(f"  Target:      {target}")
    print(
        f"  Tracker:     {values['TRACKER_PLATFORM']}"
        + (f" ({values['TRACKER_REPO']})" if values["TRACKER_REPO"] else "")
    )
    print(f"  ID prefix:   {values['ID_PREFIX']}")
    print()
    print("  Created:")
    print("    .flow/            playbook, steps, templates, guardrails, config.yaml")
    print("    .claude/          agents, commands, hooks, settings.json")
    print("    knowledge/        map + decisions scaffolding")
    print("    .mcp.json         MCP server wiring (repo root)")
    print("    worklog/          per-ticket worklogs land here")
    print()
    print("  Prerequisites (install once in Claude Code — not repo-local):")
    print("    /plugin install superpowers        — the per-phase skills Flow invokes")
    print("    /plugin install pr-review-toolkit  — the Ship branch-hardening review agents")
    print("    uv tool install \"graphifyy[mcp]\"   — the code-graph backend (or run `flow setup`)")
    print("    (`flow doctor` verifies these are present)")
    print()
    print("  Next steps:")
    print("    flow doctor       — health-check the install and integrations")
    print("    flow check        — run the quality gate")
    print("    /flow-scope       — the Claude Code entrypoint for a new idea")
