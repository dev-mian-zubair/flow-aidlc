"""Flow CLI — `flow <command>`.

Thin argparse dispatcher. Each subcommand lives in ``flow_aidlc.commands.<name>``
and exposes ``run(args) -> int``. Handlers are imported lazily so a stubbed or
heavy command never slows down `flow version`.
"""
from __future__ import annotations

import argparse
import importlib
import sys

from flow_aidlc import __version__

# subcommand -> (module under flow_aidlc.commands, help text)
_COMMANDS: dict[str, tuple[str, str]] = {
    "init": ("init", "Scaffold the Flow instance into the current repo"),
    "setup": ("setup", "One-command onboarding: graph tool + graph build + doctor"),
    "guardrail": ("guardrail", "Author guardrails (e.g. `flow guardrail add <name>`)"),
    "map": ("map", "Manage knowledge maps (e.g. `flow map add <glob> <doc>`)"),
    "doctor": ("doctor", "Health-check the install and integrations"),
    "check": ("check", "Run the quality gate"),
    "ci": ("ci", "Scaffold CI that runs the quality gate (e.g. `flow ci init`)"),
    "status": ("status", "Show where each ticket sits in the Scope→Shape→Build→Ship pipeline"),
    "learnings": ("learnings", "Surface candidate learnings from worklog journals (`--promote` to record)"),
    "selftest": ("selftest", "Run the mechanical offline self-test"),
    "refresh": ("refresh", "Rebuild the code graph (structure freshness); /flow-refresh curates invariants"),
    "plugin": ("plugin", "Build the Claude Code plugin (e.g. `flow plugin build`)"),
    "secrets": ("secrets", "Route MCP secrets through a secrets manager (e.g. `flow secrets use infisical`)"),
    "upgrade": ("upgrade", "Update engine assets without touching your instance"),
    "version": ("version", "Print the engine version"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flow",
        description="Flow — a governed AI-DLC methodology (Scope -> Shape -> Build -> Ship).",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"flow {__version__}"
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    for name, (_module, help_text) in _COMMANDS.items():
        sp = sub.add_parser(name, help=help_text, add_help=True)
        # Each command parses its own remaining args from argv to stay decoupled.
        sp.set_defaults(_command=name)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()

    if not argv:
        parser.print_help()
        return 0

    command = argv[0]
    if command in ("-h", "--help"):
        parser.print_help()
        return 0
    if command in ("-V", "--version"):
        print(f"flow {__version__}")
        return 0

    if command not in _COMMANDS:
        sys.stderr.write(f"flow: unknown command '{command}'\n\n")
        parser.print_help()
        return 2

    module_name, _ = _COMMANDS[command]
    try:
        module = importlib.import_module(f"flow_aidlc.commands.{module_name}")
    except ModuleNotFoundError:
        sys.stderr.write(f"flow: command '{command}' is not available yet\n")
        return 2

    # The handler receives the remaining argv (everything after the subcommand).
    return int(module.run(argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
