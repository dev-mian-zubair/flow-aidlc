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
    sub = p.add_subparsers(dest="action", required=True)
    u = sub.add_parser("use", help="Wrap secret-bearing servers with a provider.")
    u.add_argument("provider")
    u.add_argument("--env", default=None, help="Provider environment (e.g. prod).")
    u.add_argument("--dry-run", action="store_true")
    u.add_argument("--path", default=None, dest="path", help="Repo dir (default: search up from cwd).")
    off = sub.add_parser("off", help="Unwrap all wrapped servers.")
    off.add_argument("--dry-run", action="store_true")
    off.add_argument("--path", default=None, dest="path", help="Repo dir (default: search up from cwd).")
    st = sub.add_parser("status", help="Report the credential wiring per server.")
    st.add_argument("--path", default=None, dest="path", help="Repo dir (default: search up from cwd).")
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
            print(f'  {provider_name} run -- <original command + args>')
            return 2
        sys.stderr.write(f"flow secrets: unknown provider '{provider_name}'\n")
        return 2

    mcp_path, mcp = _load(root)
    if mcp is None:
        return 2
    servers = mcp.get("mcpServers") or {}
    targets = list(mc.secret_vars(mcp).keys())
    to_wrap = [n for n in targets if not mc.is_wrapped(servers[n])]

    if not targets:
        print("No secret-bearing servers in .mcp.json — nothing to wrap.")
        return 0

    for note in provider.preconditions(root):
        print(f"  [note] {note}")

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


def _status(root: Path) -> int:
    print("flow secrets status: not implemented yet")
    return 0
