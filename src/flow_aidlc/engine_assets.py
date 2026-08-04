"""Engine-asset helpers — locate the packaged engine and render its templates.

The engine (playbook, steps, templates, Claude wiring, knowledge scaffolding)
ships as package data beside this module at ``flow_aidlc/engine/``. `flow init`
copies it into a target repo; three ``.tmpl`` config files carry ``{{TOKEN}}``
placeholders that get substituted here from project-specific values.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

# Every ``{{TOKEN}}`` the engine's .tmpl files reference, with a safe default.
# `flow init` starts from these and overrides from CLI flags / prompts.
TOKEN_DEFAULTS: dict[str, str] = {
    "TRACKER_PLATFORM": "github",
    "TRACKER_MCP": "github",
    "TRACKER_REPO": "",
    "ID_PREFIX": "PI",
    "TEST_CMD": "",
    "BUILD_CMD": "",
    "LINT_CMD": "",
    "TYPECHECK_CMD": "",
    "FLOW_DB_READONLY_URI": "",
}

_TOKEN_RE = re.compile(r"\{\{([A-Z_]+)\}\}")


def engine_dir() -> Path:
    """Absolute path to the packaged engine assets (``flow_aidlc/engine/``)."""
    return Path(__file__).resolve().parent / "engine"


def render(text: str, values: dict[str, str]) -> str:
    """Replace every ``{{TOKEN}}`` in ``text`` with ``values.get(TOKEN, "")``.

    Deterministic and eval-free: an unknown token renders to the empty string
    rather than being left as a literal placeholder.
    """
    return _TOKEN_RE.sub(lambda m: values.get(m.group(1), ""), text)


def merge_settings(engine_settings: Path, target_settings: Path) -> None:
    """Deep-merge the engine's hooks into an existing settings.json, or copy it.

    Appends engine hook entries under each event key without duplicating an
    identical command, and preserves the user's other top-level keys. Shared by
    ``flow init`` (first scaffold) and ``flow upgrade`` (re-merge new hooks into
    the user's evolved settings) so the two stay in lock-step.
    """
    if not target_settings.exists():
        target_settings.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(engine_settings, target_settings)
        return

    engine_data = json.loads(engine_settings.read_text(encoding="utf-8"))
    try:
        user_data = json.loads(target_settings.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # Unparseable user settings: don't clobber; leave engine hooks unmerged.
        sys.stderr.write(
            f"WARNING: {target_settings} is not valid JSON — leaving it untouched.\n"
        )
        return

    user_hooks = user_data.setdefault("hooks", {})
    for event, engine_groups in engine_data.get("hooks", {}).items():
        existing_groups = user_hooks.setdefault(event, [])
        existing_cmds = {
            h.get("command")
            for group in existing_groups
            for h in group.get("hooks", [])
        }
        for group in engine_groups:
            new_hooks = [
                h for h in group.get("hooks", [])
                if h.get("command") not in existing_cmds
            ]
            if not new_hooks:
                continue
            merged_group = dict(group)
            merged_group["hooks"] = new_hooks
            existing_groups.append(merged_group)
            existing_cmds.update(h.get("command") for h in new_hooks)

    target_settings.write_text(json.dumps(user_data, indent=2) + "\n", encoding="utf-8")
