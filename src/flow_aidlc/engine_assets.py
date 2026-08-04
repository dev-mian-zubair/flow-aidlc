"""Engine-asset helpers — locate the packaged engine and render its templates.

The engine (playbook, steps, templates, Claude wiring, knowledge scaffolding)
ships as package data beside this module at ``flow_aidlc/engine/``. `flow init`
copies it into a target repo; three ``.tmpl`` config files carry ``{{TOKEN}}``
placeholders that get substituted here from project-specific values.
"""
from __future__ import annotations

import re
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
