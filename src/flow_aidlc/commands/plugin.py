"""`flow plugin build` — assemble the Claude Code plugin from the engine assets.

The engine's Claude Code surface (``/flow-*`` commands, the phase agents, the
hook scripts, and the hooks wiring in ``settings.json``) is the single source of
truth at ``flow_aidlc/engine/claude/``. This command mechanically re-assembles
that surface into an installable Claude Code plugin tree under ``plugin/`` — so
``plugin/`` is a *build artifact*, never hand-edited.

What it produces (see ``docs/m6-plugin-report.md`` for the observed schema):

    plugin/
      .claude-plugin/plugin.json    manifest (name/version/description/author)
      commands/*.md                 the /flow-* commands (flattened, verbatim)
      agents/*.md                   the phase agents (flattened, verbatim)
      hooks/*.sh                    hook scripts (+ _lib.sh), kept executable
      hooks/hooks.json              settings.json hooks -> plugin hooks format
      README.md                     install + composition note

And, at the repo root, ``.claude-plugin/marketplace.json`` listing this one
plugin so `/plugin marketplace add <repo>` finds it.

Composition model: the *plugin* provides the Claude Code surface; the *`flow`
CLI* provides `flow init` (per-project scaffolding) and `flow check` (the gate).
A user installs the plugin AND runs `flow init` in their repo — the hooks and
commands operate on the ``.flow/`` instance that `flow init` creates.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import stat
from pathlib import Path

from flow_aidlc import __version__
from flow_aidlc.engine_assets import engine_dir

# The engine references its hook scripts by the in-repo path a `flow init`
# install lays down (``.claude/hooks/foo.sh``). Inside a plugin the same scripts
# live under the plugin root, addressed via Claude Code's ``${CLAUDE_PLUGIN_ROOT}``
# convention. This rewrites the former into the latter.
_HOOK_PATH_RE = re.compile(r"\.claude/hooks/([A-Za-z0-9_.-]+)")
_PLUGIN_HOOK_PREFIX = "${CLAUDE_PLUGIN_ROOT}/hooks/"

_PLUGIN_NAME = "flow"
_PLUGIN_DESCRIPTION = (
    "The Flow AI-DLC methodology as a Claude Code surface: the /flow-* commands, "
    "the delivery phase agents (Scope -> Shape -> Build -> Ship), a greenfield "
    "product-definition Discover phase (/flow-discover), and the governance hooks. "
    "Pairs with the `flow` CLI — run `flow init` in your repo to scaffold the "
    ".flow/ instance these commands and hooks operate on."
)
_PLUGIN_AUTHOR = {"name": "Flow (flow-aidlc)"}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="flow plugin build",
        description="Assemble the Claude Code plugin tree from the engine assets.",
    )
    p.add_argument(
        "--out",
        default=None,
        help="Output directory for the plugin tree (default: <repo>/plugin).",
    )
    return p


def run(argv: list[str]) -> int:
    # Support `flow plugin build ...` (the documented form) as well as a bare
    # `flow plugin ...` that defaults to build.
    if argv and argv[0] == "build":
        argv = argv[1:]
    elif argv and argv[0] in ("-h", "--help"):
        _build_parser().parse_args(argv)
        return 0

    args = _build_parser().parse_args(argv)

    eng_claude = engine_dir() / "claude"
    out = _resolve_out(args.out)

    _reset_dir(out)
    n_commands = _copy_flat_md(eng_claude / "commands", out / "commands")
    n_agents = _copy_flat_md(eng_claude / "agents", out / "agents")
    n_hooks = _build_hooks(eng_claude, out / "hooks")
    _write_plugin_manifest(out / ".claude-plugin" / "plugin.json")
    _write_readme(out / "README.md")
    _write_marketplace(out)

    print(f"Built Flow plugin at {out}")
    print(f"  commands: {n_commands}")
    print(f"  agents:   {n_agents}")
    print(f"  hooks:    {n_hooks}")
    print(f"  version:  {__version__}")
    return 0


# ---------------------------------------------------------------------------
# path resolution
# ---------------------------------------------------------------------------

def _repo_root() -> Path:
    """The flow-aidlc repo root (three parents up: commands/ -> flow_aidlc/ ->
    src/ -> repo)."""
    return Path(__file__).resolve().parents[3]


def _resolve_out(out_arg: str | None) -> Path:
    if out_arg:
        return Path(out_arg).resolve()
    return _repo_root() / "plugin"


# ---------------------------------------------------------------------------
# assembly steps
# ---------------------------------------------------------------------------

def _reset_dir(out: Path) -> None:
    """Clear an existing plugin tree so the build is deterministic/idempotent."""
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)


def _copy_flat_md(src_root: Path, dst: Path) -> int:
    """Copy every ``*.md`` under ``src_root`` (recursively) into a *flat* ``dst``.

    Claude Code discovers commands/agents by conventional directory; the engine
    nests agents by phase (scope/, shape/, ...) but the plugin surface is flat.
    Basenames are unique across the engine, so flattening is loss-free.
    """
    dst.mkdir(parents=True, exist_ok=True)
    count = 0
    seen: set[str] = set()
    for md in sorted(src_root.rglob("*.md")):
        if md.name in seen:
            raise RuntimeError(f"duplicate basename while flattening: {md.name}")
        seen.add(md.name)
        shutil.copy2(md, dst / md.name)
        count += 1
    return count


def _build_hooks(eng_claude: Path, dst: Path) -> int:
    """Copy hook scripts (executable) and translate settings.json -> hooks.json.

    Returns the number of hook *entries* wired in hooks.json (7 — one per event;
    ``_lib.sh`` is a shared library, not a hook, so it is copied but not counted).
    """
    dst.mkdir(parents=True, exist_ok=True)

    # 1. Copy every hook script verbatim, keeping the executable bit.
    for sh in sorted((eng_claude / "hooks").glob("*.sh")):
        target = dst / sh.name
        shutil.copy2(sh, target)
        mode = target.stat().st_mode
        target.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # 2. Translate the engine settings.json hooks block into hooks.json, rewriting
    #    each ``.claude/hooks/foo.sh`` command to ``${CLAUDE_PLUGIN_ROOT}/hooks/foo.sh``.
    settings = json.loads((eng_claude / "settings.json").read_text(encoding="utf-8"))
    hooks_block = settings.get("hooks", {})

    entry_count = 0
    for groups in hooks_block.values():
        for group in groups:
            for hook in group.get("hooks", []):
                cmd = hook.get("command", "")
                hook["command"] = _HOOK_PATH_RE.sub(
                    lambda m: _PLUGIN_HOOK_PREFIX + m.group(1), cmd
                )
                entry_count += 1

    hooks_json = {
        "description": (
            "Flow governance hooks — journals prompts, guards scope, holds "
            "checkpoints, saves on compaction, and flags stale knowledge. "
            "Translated from the engine settings.json; scripts resolve under "
            "${CLAUDE_PLUGIN_ROOT}/hooks/."
        ),
        "hooks": hooks_block,
    }
    (dst / "hooks.json").write_text(
        json.dumps(hooks_json, indent=2) + "\n", encoding="utf-8"
    )
    return entry_count


def _write_plugin_manifest(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": _PLUGIN_NAME,
        "version": __version__,
        "description": _PLUGIN_DESCRIPTION,
        "author": _PLUGIN_AUTHOR,
    }
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _write_marketplace(out: Path) -> None:
    """Write ``.claude-plugin/marketplace.json`` next to the plugin dir.

    When ``--out`` is the default ``<repo>/plugin``, this lands at the repo root
    (``<repo>/.claude-plugin/marketplace.json``) with ``source: "./plugin"`` so
    ``/plugin marketplace add <repo>`` resolves it. For a custom ``--out``, the
    marketplace is written beside the plugin dir pointing at ``./<dirname>``.
    """
    marketplace_root = out.parent / ".claude-plugin"
    marketplace_root.mkdir(parents=True, exist_ok=True)
    marketplace = {
        "name": "flow-aidlc",
        "description": "The Flow AI-DLC methodology as a Claude Code plugin.",
        "owner": _PLUGIN_AUTHOR,
        "plugins": [
            {
                "name": _PLUGIN_NAME,
                "description": _PLUGIN_DESCRIPTION,
                "version": __version__,
                "source": f"./{out.name}",
                "author": _PLUGIN_AUTHOR,
            }
        ],
    }
    (marketplace_root / "marketplace.json").write_text(
        json.dumps(marketplace, indent=2) + "\n", encoding="utf-8"
    )


_README = """\
# Flow — Claude Code plugin

This is the **Claude Code surface** of [Flow](../README.md), the governed AI-DLC
methodology: the `/flow-*` slash commands, the phase agents (Scope → Shape →
Build → Ship), and the governance hooks.

> This directory is a **build artifact**. It is regenerated from the engine
> assets (`src/flow_aidlc/engine/claude/`) by `flow plugin build`. Don't edit it
> by hand — edit the engine and rebuild.

## Composition: plugin **+** `flow init`

Flow has two halves that work together:

| Half | Provides | How you get it |
|---|---|---|
| **This plugin** | the Claude Code surface: `/flow-*` commands, phase agents, hooks | `/plugin install flow` |
| **The `flow` CLI** | per-project scaffolding (`flow init`) and the quality gate (`flow check`) | `pipx install flow-aidlc` |

The hooks and commands in this plugin operate on the **`.flow/` instance** that
`flow init` creates in your repo. Install the plugin **and** run `flow init` —
neither half is useful without the other.

## Install

From this repo (local marketplace):

```
# In Claude Code:
/plugin marketplace add /absolute/path/to/flow-aidlc
/plugin install flow
```

`/plugin marketplace add` reads `.claude-plugin/marketplace.json` at the repo
root, which lists this one plugin (`source: "./plugin"`).

Then, in your target repo:

```
pipx install flow-aidlc      # the CLI half
cd your-repo
flow init                    # scaffold .flow/ (+ docs/flow/knowledge/, config)
flow doctor                  # verify the install
```

Now the `/flow-*` commands and the hooks act on that `.flow/` instance.

## What's inside

- `commands/` — the `/flow-*` slash commands.
- `agents/` — the phase agents (scope / shape / build / review / knowledge).
- `hooks/` — the hook scripts and `hooks.json` (wired to `SessionStart`,
  `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`,
  `PreCompact`). Scripts resolve via `${CLAUDE_PLUGIN_ROOT}/hooks/`.
- `.claude-plugin/plugin.json` — the plugin manifest.

## Regenerate

```
flow plugin build            # rewrites ./plugin from the engine
flow plugin build --out /tmp/x   # build elsewhere (idempotent)
```
"""


def _write_readme(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_README, encoding="utf-8")
