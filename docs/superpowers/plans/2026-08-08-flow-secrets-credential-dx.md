# flow secrets — Credential DX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `flow secrets` command that routes every secret-bearing MCP server through a secrets manager (Infisical first), plus a `.env` fallback scaffolded by `flow init` and a mode-aware credential check in `flow doctor`.

**Architecture:** A new pure-function module (`mcp_config.py`) scans `.mcp.json` for `${VAR}` secrets and performs lossless wrap/unwrap (stashing originals under a `_flowWrapped` key). A new `flow secrets` command (provider registry, Infisical implemented) drives wrap/unwrap and a shared credential check reused by `flow doctor`. `flow init` scaffolds `.env.example` + gitignores `.env`.

**Tech Stack:** Python 3.10+ (stdlib only: `argparse`, `json`, `re`, `subprocess`, `shutil`, `pathlib`), `pyyaml` (already a dep), `pytest` (dev).

## Global Constraints

- Python `>=3.10`; every module starts with `from __future__ import annotations`.
- Stdlib only for new runtime code (no new dependencies).
- Each command module exposes `run(argv: list[str]) -> int`; registered in `flow_aidlc/cli.py`'s `_COMMANDS` dict.
- The credential check is **WARN/PASS only — never FAIL** (`flow doctor` runs in CI where no secrets exist).
- All `.mcp.json` edits are **idempotent** and support `--dry-run` (print, write nothing).
- Secret inventory is derived by **scanning `.mcp.json` for `${VAR}` references** — the single source of truth (spec §8). A `${VAR}` is `\$\{([A-Z0-9_]+)\}`.
- The stash key is exactly `_flowWrapped`; Claude Code ignores unknown per-server keys.
- Only servers whose env block contains a `${VAR}` are wrapped; non-secret servers (`graphify`, `context7`) are untouched.
- JSON is written with `json.dumps(obj, indent=2) + "\n"`, `encoding="utf-8"`.
- Reference spec: `docs/superpowers/specs/2026-08-08-flow-secrets-credential-dx-design.md`.

---

## File Structure

- **Create `src/flow_aidlc/mcp_config.py`** — pure helpers over a parsed `.mcp.json`: secret-var scanning, `is_wrapped`, `wrap_server`, `unwrap_server`. No I/O beyond an explicit `load_mcp`/`dump_mcp`. (Task 1)
- **Create `src/flow_aidlc/commands/secrets.py`** — the `flow secrets use/off/status` command, the provider registry (Infisical), and the shared `credential_report()` / `secrets_summary()` functions. (Tasks 2–3)
- **Modify `src/flow_aidlc/cli.py`** — register the `secrets` subcommand. (Task 2)
- **Modify `src/flow_aidlc/commands/doctor.py`** — add a `secrets` check line calling `secrets_summary()`. (Task 4)
- **Modify `src/flow_aidlc/commands/init.py`** — scaffold `.env.example` from `all_secret_vars`, add `.env` to gitignore. (Task 5)
- **Modify `src/flow_aidlc/engine/flow/INTEGRATIONS.md`** + **`README.md`** — document `flow secrets` + the credential ladder. (Task 6)
- **Tests:** `tests/test_mcp_config.py` (new), `tests/test_secrets.py` (new), extend `tests/test_doctor.py`, `tests/test_init.py`.

---

## Task 1: `mcp_config.py` — secret scanning + wrap/unwrap

**Files:**
- Create: `src/flow_aidlc/mcp_config.py`
- Test: `tests/test_mcp_config.py`

**Interfaces:**
- Produces:
  - `load_mcp(path: Path) -> dict`
  - `dump_mcp(path: Path, mcp: dict) -> None`
  - `secret_vars(mcp: dict) -> dict[str, list[str]]` — server name → sorted unique `${VAR}` names, only for secret-bearing servers
  - `all_secret_vars(mcp: dict) -> list[str]` — flat sorted unique
  - `is_wrapped(server: dict) -> bool`
  - `wrap_server(server: dict, cli: str, run_args: list[str]) -> dict`
  - `unwrap_server(server: dict) -> dict`
  - Constant `STASH_KEY = "_flowWrapped"`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_mcp_config.py
from flow_aidlc import mcp_config as mc

def _mcp():
    return {"mcpServers": {
        "github": {"command": "npx", "args": ["-y", "srv-github"],
                    "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}},
        "graphify": {"command": "graphify-mcp", "args": ["graph.json"]},
        "pg": {"command": "npx", "args": ["pg"],
                "env": {"FLOW_DB_READONLY_URI": "${FLOW_DB_READONLY_URI}"}},
    }}

def test_secret_vars_only_secret_bearing_servers():
    assert mc.secret_vars(_mcp()) == {
        "github": ["GITHUB_TOKEN"], "pg": ["FLOW_DB_READONLY_URI"]}

def test_all_secret_vars_flat_sorted_unique():
    assert mc.all_secret_vars(_mcp()) == ["FLOW_DB_READONLY_URI", "GITHUB_TOKEN"]

def test_wrap_then_is_wrapped_and_drops_env():
    w = mc.wrap_server(_mcp()["mcpServers"]["github"], "infisical", ["run"])
    assert mc.is_wrapped(w)
    assert w["command"] == "infisical"
    assert w["args"] == ["run", "--", "npx", "-y", "srv-github"]
    assert "env" not in w
    assert w[mc.STASH_KEY]["env"] == {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}

def test_wrap_is_idempotent():
    once = mc.wrap_server(_mcp()["mcpServers"]["github"], "infisical", ["run"])
    twice = mc.wrap_server(once, "infisical", ["run"])
    assert twice == once

def test_wrap_with_env_flag():
    w = mc.wrap_server(_mcp()["mcpServers"]["github"], "infisical", ["run", "--env", "prod"])
    assert w["args"][:4] == ["run", "--env", "prod", "--"]

def test_unwrap_round_trips_exactly():
    orig = _mcp()["mcpServers"]["github"]
    assert mc.unwrap_server(mc.wrap_server(orig, "infisical", ["run"])) == orig

def test_unwrap_preserves_custom_keys_and_args():
    custom = {"command": "npx", "args": ["a", "b"],
              "env": {"T": "${T}", "EXTRA": "literal"}, "cwd": "/x"}
    assert mc.unwrap_server(mc.wrap_server(custom, "infisical", ["run"])) == custom

def test_unwrap_noop_when_not_wrapped():
    plain = _mcp()["mcpServers"]["graphify"]
    assert mc.unwrap_server(plain) == plain

def test_secret_vars_stable_after_wrap():
    m = _mcp()
    m["mcpServers"]["github"] = mc.wrap_server(m["mcpServers"]["github"], "infisical", ["run"])
    assert "GITHUB_TOKEN" in mc.secret_vars(m)["github"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_mcp_config.py -q`
Expected: FAIL with `ModuleNotFoundError: flow_aidlc.mcp_config`
(Use `uv run --with pytest --with pyyaml python -m pytest ...` if pytest isn't on PATH.)

- [ ] **Step 3: Write the implementation**

```python
# src/flow_aidlc/mcp_config.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_mcp_config.py -q`
Expected: PASS (all 9)

- [ ] **Step 5: Commit**

```bash
git add src/flow_aidlc/mcp_config.py tests/test_mcp_config.py
git commit -m "feat(secrets): mcp_config — secret-var scan + wrap/unwrap helpers"
```

---

## Task 2: `flow secrets use/off` + provider registry + CLI registration

**Files:**
- Create: `src/flow_aidlc/commands/secrets.py`
- Modify: `src/flow_aidlc/cli.py` (add to `_COMMANDS`)
- Test: `tests/test_secrets.py`

**Interfaces:**
- Consumes: `flow_aidlc.mcp_config` (Task 1); `flow_aidlc.checks._root.find_repo_root`
- Produces:
  - `run(argv: list[str]) -> int`
  - `Provider` dataclass with `.cli: str`, `.run_args(env: str | None) -> list[str]`, `.preconditions(root: Path) -> list[str]`, `.probe(root: Path) -> bool`
  - `_PROVIDERS: dict[str, Provider]` (key `"infisical"`)
  - `_GUIDED_ONLY: set[str]` (`{"op", "1password", "doppler"}`)

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_secrets.py
import json
from pathlib import Path

from flow_aidlc.commands import secrets

def _write_mcp(root: Path, wrapped_github=False):
    root.mkdir(parents=True, exist_ok=True)
    mcp = {"mcpServers": {
        "github": {"command": "npx", "args": ["-y", "srv-github"],
                    "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}},
        "graphify": {"command": "graphify-mcp", "args": ["graph.json"]},
    }}
    (root / ".mcp.json").write_text(json.dumps(mcp, indent=2) + "\n")
    return root / ".mcp.json"

def _servers(path: Path):
    return json.loads(path.read_text())["mcpServers"]

def test_use_wraps_all_secret_servers_leaves_others(tmp_path):
    p = _write_mcp(tmp_path)
    assert secrets.run(["use", "infisical", "--path", str(tmp_path)]) == 0
    s = _servers(p)
    assert s["github"]["command"] == "infisical"
    assert s["github"]["args"][:3] == ["run", "--", "npx"]
    assert "_flowWrapped" in s["github"]
    assert s["graphify"]["command"] == "graphify-mcp"   # untouched
    assert "_flowWrapped" not in s["graphify"]

def test_use_is_idempotent(tmp_path):
    p = _write_mcp(tmp_path)
    secrets.run(["use", "infisical", "--path", str(tmp_path)])
    first = p.read_text()
    assert secrets.run(["use", "infisical", "--path", str(tmp_path)]) == 0
    assert p.read_text() == first

def test_off_restores_original(tmp_path):
    p = _write_mcp(tmp_path)
    before = p.read_text()
    secrets.run(["use", "infisical", "--path", str(tmp_path)])
    assert secrets.run(["off", "--path", str(tmp_path)]) == 0
    assert json.loads(p.read_text()) == json.loads(before)

def test_use_dry_run_writes_nothing(tmp_path):
    p = _write_mcp(tmp_path)
    before = p.read_text()
    assert secrets.run(["use", "infisical", "--dry-run", "--path", str(tmp_path)]) == 0
    assert p.read_text() == before

def test_use_env_flag_in_wrapper(tmp_path):
    p = _write_mcp(tmp_path)
    secrets.run(["use", "infisical", "--env", "prod", "--path", str(tmp_path)])
    assert _servers(p)["github"]["args"][:4] == ["run", "--env", "prod", "--"]

def test_unknown_provider_errors(tmp_path):
    _write_mcp(tmp_path)
    assert secrets.run(["use", "bogus", "--path", str(tmp_path)]) == 2

def test_guided_only_provider_prints_pattern(tmp_path, capsys):
    _write_mcp(tmp_path)
    assert secrets.run(["use", "doppler", "--path", str(tmp_path)]) == 2
    assert "doppler run" in capsys.readouterr().out

def test_no_mcp_json_errors(tmp_path):
    assert secrets.run(["use", "infisical", "--path", str(tmp_path)]) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_secrets.py -q`
Expected: FAIL with `ModuleNotFoundError: flow_aidlc.commands.secrets`

- [ ] **Step 3: Write the implementation**

```python
# src/flow_aidlc/commands/secrets.py
"""`flow secrets` — route every secret-bearing MCP server through a secrets
manager instead of shell / .env environment variables.

    flow secrets use <provider> [--env NAME] [--dry-run] [--path DIR]
    flow secrets off [--dry-run] [--path DIR]
    flow secrets status [--path DIR]

Infisical is implemented first-class; op/doppler are recognised and print the
manual wrapper pattern. Only servers with a ``${VAR}`` env block are wrapped.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from flow_aidlc import mcp_config as mc
from flow_aidlc.checks._root import find_repo_root

PASS, WARN = "PASS", "WARN"


@dataclass(frozen=True)
class Provider:
    name: str
    cli: str
    project_marker: str  # e.g. ".infisical.json"

    def run_args(self, env: str | None) -> list[str]:
        return ["run", *(["--env", env] if env else [])]

    def preconditions(self, root: Path) -> list[str]:
        problems: list[str] = []
        if not shutil.which(self.cli):
            problems.append(f"`{self.cli}` not on PATH — install it (see INTEGRATIONS.md)")
        if not (root / self.project_marker).exists():
            problems.append(f"no {self.project_marker} — run `{self.cli} init` to link the project")
        return problems

    def probe(self, root: Path) -> bool:
        """Deep check: can the CLI actually resolve secrets? (network)."""
        if not shutil.which(self.cli):
            return False
        try:
            r = subprocess.run(
                [self.cli, "secrets", "--silent"],
                cwd=str(root), capture_output=True, timeout=15,
            )
            return r.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False


_PROVIDERS: dict[str, Provider] = {
    "infisical": Provider(name="infisical", cli="infisical", project_marker=".infisical.json"),
}
_GUIDED_ONLY = {"op", "1password", "doppler"}


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="flow secrets",
                                description="Route MCP secrets through a secrets manager.")
    p.add_argument("--path", default=None, help="Repo dir (default: search up from cwd).")
    sub = p.add_subparsers(dest="action", required=True)
    u = sub.add_parser("use", help="Wrap secret-bearing servers with a provider.")
    u.add_argument("provider")
    u.add_argument("--env", default=None, help="Provider environment (e.g. prod).")
    u.add_argument("--dry-run", action="store_true")
    off = sub.add_parser("off", help="Unwrap all wrapped servers.")
    off.add_argument("--dry-run", action="store_true")
    sub.add_parser("status", help="Report the credential wiring per server.")
    return p


def run(argv: list[str]) -> int:
    try:
        args = _parser().parse_args(argv)
    except SystemExit:
        return 2
    root = find_repo_root(args.path)
    if args.action == "use":
        return _use(root, args.provider, args.env, args.dry_run)
    if args.action == "off":
        return _off(root, args.dry_run)
    if args.action == "status":
        return _status(root)
    return 2


def _load(root: Path):
    mcp_path = root / ".mcp.json"
    if not mcp_path.exists():
        sys.stderr.write("flow secrets: no .mcp.json — run `flow init` first\n")
        return None, None
    return mcp_path, mc.load_mcp(mcp_path)


def _use(root: Path, provider_name: str, env: str | None, dry: bool) -> int:
    provider = _PROVIDERS.get(provider_name)
    if provider is None:
        if provider_name in _GUIDED_ONLY:
            print(f"{provider_name}: not wired first-class yet. Wrap a server manually:")
            print(f'  "command": "{provider_name}", "args": ["run", "--", "<original command + args>"]')
            return 2
        sys.stderr.write(f"flow secrets: unknown provider '{provider_name}'\n")
        return 2

    mcp_path, mcp = _load(root)
    if mcp is None:
        return 2
    servers = mcp.get("mcpServers") or {}
    targets = list(mc.secret_vars(mcp).keys())
    to_wrap = [n for n in targets if not mc.is_wrapped(servers[n])]

    for note in provider.preconditions(root):
        print(f"  [note] {note}")

    if not targets:
        print("No secret-bearing servers in .mcp.json — nothing to wrap.")
        return 0
    if not to_wrap:
        print("All secret-bearing servers already wrapped.")
        return 0
    if dry:
        print("DRY-RUN: would wrap " + ", ".join(to_wrap))
        return 0
    for name in to_wrap:
        servers[name] = mc.wrap_server(servers[name], provider.cli, provider.run_args(env))
    mc.dump_mcp(mcp_path, mcp)
    print(f"Wrapped via {provider.name}: " + ", ".join(to_wrap))
    print("Reload MCP servers in your client for the change to take effect.")
    return 0


def _off(root: Path, dry: bool) -> int:
    mcp_path, mcp = _load(root)
    if mcp is None:
        return 2
    servers = mcp.get("mcpServers") or {}
    wrapped = [n for n, s in servers.items() if mc.is_wrapped(s)]
    if not wrapped:
        print("No wrapped servers — nothing to unwrap.")
        return 0
    if dry:
        print("DRY-RUN: would unwrap " + ", ".join(wrapped))
        return 0
    for name in wrapped:
        servers[name] = mc.unwrap_server(servers[name])
    mc.dump_mcp(mcp_path, mcp)
    print("Unwrapped: " + ", ".join(wrapped))
    return 0
```

(`_status` is added in Task 3 — add a temporary stub so the module imports:)

```python
def _status(root: Path) -> int:
    print("flow secrets status: not implemented yet")
    return 0
```

- [ ] **Step 4: Register the command in the CLI**

Modify `src/flow_aidlc/cli.py` — add to the `_COMMANDS` dict (after `"plugin"`):

```python
    "secrets": ("secrets", "Route MCP secrets through a secrets manager (e.g. `flow secrets use infisical`)"),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_secrets.py -q`
Expected: PASS (all 8)

- [ ] **Step 6: Commit**

```bash
git add src/flow_aidlc/commands/secrets.py src/flow_aidlc/cli.py tests/test_secrets.py
git commit -m "feat(secrets): flow secrets use/off + provider registry (infisical)"
```

---

## Task 3: `flow secrets status` + shared credential check

**Files:**
- Modify: `src/flow_aidlc/commands/secrets.py` (replace the `_status` stub; add `credential_report` + `secrets_summary`)
- Test: `tests/test_secrets.py` (add credential-check tests)

**Interfaces:**
- Produces:
  - `credential_report(root: Path, deep: bool = False) -> list[tuple[str, str, str]]` — `(server, status, detail)` rows for each secret-bearing server; `status` in `{PASS, WARN}`
  - `secrets_summary(root: Path) -> tuple[str, str]` — `(overall_status, detail)` aggregate for `flow doctor`
  - `_parse_env_file(path: Path) -> dict[str, str]`

- [ ] **Step 1: Write the failing tests**

```python
# add to tests/test_secrets.py
import os

def test_summary_var_mode_all_set(tmp_path, monkeypatch):
    _write_mcp(tmp_path)
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    status, _ = secrets.secrets_summary(tmp_path)
    assert status == "PASS"

def test_summary_var_mode_missing_warns(tmp_path, monkeypatch):
    _write_mcp(tmp_path)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    status, detail = secrets.secrets_summary(tmp_path)
    assert status == "WARN"
    assert "GITHUB_TOKEN" in detail

def test_summary_dotenv_present_but_not_loaded(tmp_path, monkeypatch):
    _write_mcp(tmp_path)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    (tmp_path / ".env").write_text("GITHUB_TOKEN=abc\n")
    status, detail = secrets.secrets_summary(tmp_path)
    assert status == "WARN"
    assert "not loaded" in detail.lower()

def test_summary_wrapped_mode_reports_provider(tmp_path, monkeypatch):
    _write_mcp(tmp_path)
    secrets.run(["use", "infisical", "--path", str(tmp_path)])
    monkeypatch.setattr(secrets.shutil, "which", lambda c: "/usr/bin/infisical")
    (tmp_path / ".infisical.json").write_text("{}")
    status, detail = secrets.secrets_summary(tmp_path)
    assert status == "PASS"
    assert "infisical" in detail

def test_parse_env_file_ignores_comments(tmp_path):
    (tmp_path / ".env").write_text("# c\n\nA=1\nB = two \n")
    assert secrets._parse_env_file(tmp_path / ".env") == {"A": "1", "B": "two"}

def test_status_command_runs(tmp_path):
    _write_mcp(tmp_path)
    assert secrets.run(["status", "--path", str(tmp_path)]) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_secrets.py -k "summary or parse_env or status_command" -q`
Expected: FAIL (`AttributeError`/stub returns wrong content)

- [ ] **Step 3: Write the implementation**

Replace the `_status` stub and add the shared check to `secrets.py`:

```python
import os  # add to imports at top


def _parse_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip()
    return out


def _known_provider_for(server: dict) -> Provider | None:
    """If a server is wrapped by a known provider, return that Provider."""
    if not mc.is_wrapped(server):
        return None
    cli = server.get("command")
    for prov in _PROVIDERS.values():
        if prov.cli == cli:
            return prov
    return None


def credential_report(root: Path, deep: bool = False) -> list[tuple[str, str, str]]:
    """Per secret-bearing server, return (server, status, detail). WARN/PASS only."""
    mcp_path = root / ".mcp.json"
    if not mcp_path.exists():
        return []
    mcp = mc.load_mcp(mcp_path)
    inventory = mc.secret_vars(mcp)
    servers = mcp.get("mcpServers") or {}
    dotenv = _parse_env_file(root / ".env") if (root / ".env").exists() else {}

    rows: list[tuple[str, str, str]] = []
    for name, vars_ in inventory.items():
        server = servers[name]
        prov = _known_provider_for(server)
        if prov is not None:
            missing = prov.preconditions(root)
            if missing:
                rows.append((name, WARN, f"{prov.name}: " + "; ".join(missing)))
            elif deep and not prov.probe(root):
                rows.append((name, WARN, f"{prov.name}: CLI present but secrets did not resolve"))
            else:
                rows.append((name, PASS, f"{prov.name} (all vars injected at launch)"))
            continue
        # plain ${VAR} mode
        unset = [v for v in vars_ if not os.environ.get(v)]
        if not unset:
            rows.append((name, PASS, "env vars set: " + ", ".join(vars_)))
        elif all(v in dotenv for v in unset):
            rows.append((name, WARN, ".env present but not loaded — source it or use direnv "
                                     f"(unset: {', '.join(unset)})"))
        else:
            rows.append((name, WARN, "unset env vars: " + ", ".join(unset)))
    return rows


def secrets_summary(root: Path) -> tuple[str, str]:
    """Aggregate credential_report (shallow) into one (status, detail) for doctor."""
    rows = credential_report(root, deep=False)
    if not rows:
        return PASS, "no secret-bearing MCP servers"
    warns = [r for r in rows if r[1] == WARN]
    if warns:
        return WARN, "; ".join(f"{name}: {detail}" for name, _s, detail in warns)
    return PASS, ", ".join(name for name, _s, _d in rows) + " → credentials wired"


def _status(root: Path) -> int:
    rows = credential_report(root, deep=True)
    if not rows:
        print("No secret-bearing MCP servers in .mcp.json.")
        return 0
    for name, status, detail in rows:
        print(f"[{status}] {name} — {detail}")
    return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_secrets.py -q`
Expected: PASS (all)

- [ ] **Step 5: Commit**

```bash
git add src/flow_aidlc/commands/secrets.py tests/test_secrets.py
git commit -m "feat(secrets): flow secrets status + shared mode-aware credential check"
```

---

## Task 4: `flow doctor` — `secrets` check line

**Files:**
- Modify: `src/flow_aidlc/commands/doctor.py`
- Test: `tests/test_doctor.py` (add)

**Interfaces:**
- Consumes: `flow_aidlc.commands.secrets.secrets_summary` (Task 3)

- [ ] **Step 1: Write the failing tests**

```python
# add to tests/test_doctor.py
import json
from flow_aidlc.commands import doctor

def _mcp_repo(tmp_path):
    (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {
        "github": {"command": "npx", "args": ["-y", "srv"],
                    "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}}}}, indent=2))
    return tmp_path

def test_check_secrets_warns_when_unset(tmp_path, monkeypatch, capsys):
    _mcp_repo(tmp_path)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    rep = doctor._Report()
    doctor._check_secrets(rep, tmp_path)
    out = capsys.readouterr().out
    assert "[WARN]" in out and "secrets" in out
    assert rep.any_fail is False  # never FAIL

def test_check_secrets_pass_when_set(tmp_path, monkeypatch, capsys):
    _mcp_repo(tmp_path)
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    rep = doctor._Report()
    doctor._check_secrets(rep, tmp_path)
    assert "[PASS]" in capsys.readouterr().out
    assert rep.any_fail is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_doctor.py -k check_secrets -q`
Expected: FAIL (`AttributeError: _check_secrets`)

- [ ] **Step 3: Write the implementation**

In `src/flow_aidlc/commands/doctor.py`, add the call in `run()` after `_check_mcp(rep, root)`:

```python
    _check_secrets(rep, root)
```

And add the function (near `_check_mcp`):

```python
def _check_secrets(rep: _Report, root: Path) -> None:
    """Report whether each secret-bearing MCP server's credentials are wired.

    Delegates to the shared check in the secrets command (mode-aware:
    secrets-manager-wrapped vs plain ${VAR} vs .env-not-loaded). WARN, never
    FAIL — doctor runs in CI where no secret exists.
    """
    from flow_aidlc.commands.secrets import secrets_summary

    status, detail = secrets_summary(root)
    rep.line("secrets", status, detail)
```

Note: `rep.line` accepts the `PASS`/`WARN` strings returned by `secrets_summary` (they equal doctor's `PASS`/`WARN` constants).

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_doctor.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/flow_aidlc/commands/doctor.py tests/test_doctor.py
git commit -m "feat(secrets): flow doctor secrets line (mode-aware credential check)"
```

---

## Task 5: `flow init` — scaffold `.env.example` + gitignore `.env`

**Files:**
- Modify: `src/flow_aidlc/commands/init.py`
- Test: `tests/test_init.py` (add)

**Interfaces:**
- Consumes: `flow_aidlc.mcp_config.load_mcp`, `all_secret_vars` (Task 1)

- [ ] **Step 1: Write the failing tests**

```python
# add to tests/test_init.py
import subprocess
from pathlib import Path
from flow_aidlc.commands import init

def _git_init(p: Path):
    subprocess.run(["git", "init", str(p)], check=True, capture_output=True)

def test_init_scaffolds_env_example_with_tracker_vars(tmp_path):
    _git_init(tmp_path)
    assert init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)]) == 0
    example = (tmp_path / ".env.example").read_text()
    assert "GITHUB_TOKEN=" in example

def test_init_gitignores_dot_env(tmp_path):
    _git_init(tmp_path)
    init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)])
    assert ".env" in (tmp_path / ".gitignore").read_text().splitlines()

def test_init_does_not_create_real_dot_env(tmp_path):
    _git_init(tmp_path)
    init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)])
    assert not (tmp_path / ".env").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_init.py -k "env_example or dot_env" -q`
Expected: FAIL (no `.env.example`; `.env` not in `.gitignore`)

- [ ] **Step 3: Write the implementation**

In `src/flow_aidlc/commands/init.py`:

(a) Change the gitignore entry list (the `_ensure_gitignore` call) to include `.env`:

```python
    action("ensure .gitignore contains worklog/.active, .superpowers/, .env")
    if not dry:
        _ensure_gitignore(target / ".gitignore", ["worklog/.active", ".superpowers/", ".env"])
```

(b) After the `.mcp.json` render block (step 6, after `_render_file(... target / ".mcp.json" ...)`), add `.env.example` scaffolding:

```python
    # ---- .env.example (secret inventory scanned from the rendered .mcp.json) --
    action(f"write {target / '.env.example'} (required credential vars)")
    if not dry:
        _write_env_example(target)
```

(c) Add the helper (near the other `_*` helpers):

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_init.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/flow_aidlc/commands/init.py tests/test_init.py
git commit -m "feat(secrets): init scaffolds .env.example + gitignores .env"
```

---

## Task 6: Documentation — INTEGRATIONS.md + README

**Files:**
- Modify: `src/flow_aidlc/engine/flow/INTEGRATIONS.md`
- Modify: `README.md`

**Interfaces:** none (docs).

- [ ] **Step 1: Add a "Credentials & secrets" section to INTEGRATIONS.md**

Insert after the "Env vars" section (before "Verifying your setup"):

```markdown
## Credentials & secrets

Flow reads MCP credentials from the environment via `${VAR}` references in
`.mcp.json` (committed — it holds no secrets). You supply the values one of
three ways, best DX first:

1. **Secrets manager (recommended, zero plaintext)** — `flow secrets use infisical`
   rewrites every secret-bearing MCP server to `infisical run -- …`, so the
   token is injected at launch and never touches the repo, `.env`, or your
   shell. One-time: `infisical login` (stores a token in your OS keyring) +
   `infisical init` (links the project). `flow secrets off` reverts; `flow
   secrets status` verifies resolution. (`op`/`doppler` follow the same wrapper
   pattern — `flow secrets use <name>` prints it.)
2. **Provider CLI credential store** — e.g. `export GITHUB_TOKEN=$(gh auth token)`
   keeps the secret in `gh`'s store, not a file.
3. **`.env` file (fallback)** — copy the generated `.env.example` to `.env`
   (gitignored), fill it in, and load it (`direnv`, or `set -a; source .env;
   set +a`) before launching Claude Code. `flow doctor` warns if `.env` exists
   but isn't loaded.

`flow doctor` reports a `secrets` line covering every secret-bearing server;
`flow secrets status` adds a live resolve probe.
```

- [ ] **Step 2: Add a README pointer**

In `README.md`, under "What you get", add a bullet after the tracker bullet:

```markdown
- **Secrets, not in the repo** — `.mcp.json` holds only `${VAR}` references; supply values via a secrets manager (`flow secrets use infisical` — zero plaintext), a provider CLI (`gh auth token`), or a gitignored `.env`. `flow doctor` verifies they resolve.
```

- [ ] **Step 3: Verify docs don't break the gate**

Run: `python -m pytest tests/test_config_consistency.py -q`
Expected: PASS (C2 has no new repo literals — the examples use `<name>`/`o/n` placeholders, not a configured `tracker.repo`).

- [ ] **Step 4: Commit**

```bash
git add src/flow_aidlc/engine/flow/INTEGRATIONS.md README.md
git commit -m "docs(secrets): document flow secrets + the credential ladder"
```

---

## Final Verification (after all tasks)

- [ ] Run the full suite: `uv run --with pytest --with pyyaml python -m pytest -q` → all pass.
- [ ] Live smoke: `flow init --yes --repo o/n --path <tmp>` then in that dir `flow secrets use infisical --dry-run`, `flow secrets status`, `flow doctor` — inspect the `secrets` line.
- [ ] `git grep -n "TODO\|TBD" src/flow_aidlc/mcp_config.py src/flow_aidlc/commands/secrets.py` → empty.

---

## Self-Review (completed by plan author)

- **Spec coverage:** §5 command surface → Tasks 2–3; §6 wrap mechanics (`_flowWrapped`, all servers, idempotent, dry-run, provider switch) → Tasks 1–2; §7 mode-aware check (shallow/deep, mixed, WARN-only) → Tasks 3–4; §8 `.env.example` + gitignore + scan-based inventory → Tasks 1 & 5; §9 provider registry → Task 2; §10 testing → per-task tests; §11 files → matches; §12 acceptance → Final Verification.
- **Type consistency:** `wrap_server(server, cli, run_args)`, `unwrap_server(server)`, `secret_vars`/`all_secret_vars`, `credential_report(root, deep)`, `secrets_summary(root) -> (status, detail)`, `Provider.run_args/preconditions/probe`, `STASH_KEY` — used identically across tasks.
- **Placeholder scan:** no TBD/TODO; every code + test step is concrete.
- **Note:** `flow doctor` imports `secrets_summary` lazily (inside `_check_secrets`) to avoid import cost on unrelated commands, matching doctor's existing lazy-import style.
