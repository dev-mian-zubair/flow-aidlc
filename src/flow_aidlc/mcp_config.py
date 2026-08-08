"""Pure helpers over a repo's ``.mcp.json``: secret-var inventory and the
secrets-manager wrap/unwrap transforms. Kept side-effect-free (except the
explicit ``load_mcp``/``dump_mcp``) so the ``flow secrets`` command, ``flow
doctor``, and ``flow init`` can all reuse them and they stay trivially testable.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

STASH_KEY = "_flowWrapped"
_VAR_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")


def load_mcp(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_mcp(path: Path, mcp: dict) -> None:
    path.write_text(json.dumps(mcp, indent=2) + "\n", encoding="utf-8")


def _secret_env(server: dict) -> dict:
    """The env block holding this server's secrets — from the stash if wrapped."""
    if STASH_KEY in server:
        return server[STASH_KEY].get("env") or {}
    return server.get("env") or {}


def secret_vars(mcp: dict) -> dict[str, list[str]]:
    """Map each secret-bearing server name -> its sorted unique ``${VAR}`` names."""
    out: dict[str, list[str]] = {}
    for name, server in (mcp.get("mcpServers") or {}).items():
        if not isinstance(server, dict):
            continue
        found: list[str] = []
        for value in _secret_env(server).values():
            found.extend(_VAR_RE.findall(str(value)))
        if found:
            out[name] = sorted(dict.fromkeys(found))
    return out


def all_secret_vars(mcp: dict) -> list[str]:
    flat: set[str] = set()
    for names in secret_vars(mcp).values():
        flat.update(names)
    return sorted(flat)


def is_wrapped(server: dict) -> bool:
    return STASH_KEY in server


def wrap_server(server: dict, cli: str, run_args: list[str]) -> dict:
    """Return a copy of ``server`` wrapped as ``cli run ... -- <original>``.

    Stashes the original command/args/env under ``STASH_KEY`` for lossless
    unwrap and drops the top-level env (the manager injects the values).
    Idempotent: an already-wrapped server is returned unchanged.
    """
    if is_wrapped(server):
        return server
    original = {
        "provider": cli,
        "command": server.get("command"),
        "args": list(server.get("args") or []),
        "env": dict(server.get("env") or {}),
    }
    wrapped = {k: v for k, v in server.items() if k != "env"}
    wrapped["command"] = cli
    wrapped["args"] = [*run_args, "--", original["command"], *original["args"]]
    wrapped[STASH_KEY] = original
    return wrapped


def unwrap_server(server: dict) -> dict:
    """Return a copy of ``server`` restored from the stash. No-op if not wrapped."""
    if not is_wrapped(server):
        return server
    original = server[STASH_KEY]
    restored = {k: v for k, v in server.items() if k != STASH_KEY}
    restored["command"] = original.get("command")
    restored["args"] = list(original.get("args") or [])
    if original.get("env"):
        restored["env"] = dict(original["env"])
    else:
        restored.pop("env", None)
    return restored
