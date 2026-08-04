# Architecture

Flow separates cleanly into two layers. Getting this boundary right is the whole
reason the engine is portable.

## Engine vs. Instance

**The engine is generic and shipped in this package.** It contains zero
project-specific references — verified: the CLI, every check module, every Claude
Code command, and every hook are project-agnostic; they operate on *data* (config,
guardrail files, the knowledge map) rather than hardcoding any codebase.

**The instance is generated per-project by `flow init` and authored by the team.**
A project's invariants (guardrails), subsystem maps, and tracker config are the
instance — they are what makes Flow *yours*, and they are the only project-specific
files.

```
flow-aidlc (this package)                 target-repo/ (after `flow init`)
├── src/flow_aidlc/                        ├── .flow/
│   ├── cli.py            flow <cmd>       │   ├── playbook.md          (engine, copied)
│   ├── commands/         init, doctor…    │   ├── config.yaml          (INSTANCE, generated)
│   ├── checks/           gate + modules   │   ├── steps/               (engine)
│   └── engine/           bundled assets   │   ├── templates/           (engine)
│       ├── flow/                          │   ├── guardrails/
│       ├── claude/                        │   │   ├── always-on/       (INSTANCE — you author)
│       └── knowledge/                     │   │   └── optional/        (engine starters, generic)
├── pyproject.toml                         │   └── knowledge-map.yaml   (INSTANCE, generated)
└── tests/                                 ├── .claude/
                                           │   ├── commands/ agents/ hooks/  (engine)
                                           │   └── settings.json        (engine, merged)
                                           ├── knowledge/
                                           │   ├── map/                 (INSTANCE — seeded, curated)
                                           │   ├── decisions/           (INSTANCE)
                                           │   └── practices.md         (INSTANCE, seeded)
                                           └── worklog/                 (runtime, per-task)
```

## Why the boundary is clean

Flow was designed so the engine reads project facts as data:

- `config.yaml` drives which guardrails are active and the tracker/id-scheme.
- `knowledge-map.yaml` drives the freshness loop (code globs → owning doc).
- The templates drive every worklog artifact (`cp` template → fill).

Nothing project-specific is hardcoded in logic, so packaging is "move the
project data out, ship the engine, let `init` regenerate the data."

## Distribution

Two complementary channels, same engine:

1. **pip / pipx CLI** (`flow`) — install anywhere, scaffold + gate in CI. Primary.
2. **Claude Code plugin** — the `.claude/{commands,agents,hooks}` assets map
   natively onto the plugin format; the plugin surfaces `/flow-*` and calls the
   same CLI for scaffolding. (Layered on after the CLI.)

## The command surface

| Command | Purpose |
|---|---|
| `flow init` | Scaffold the instance into the current repo (interactive) |
| `flow guardrail add <name>` | Scaffold a new always-on guardrail from the template + register it |
| `flow map add <glob> <doc>` | Scaffold a knowledge/map doc + wire knowledge-map.yaml |
| `flow doctor` | Health check — hooks installed, MCP reachable, structure valid |
| `flow check` | Run the quality gate (guardrail-lint, structure, freshness, traceability) |
| `flow selftest` | Mechanical offline self-test of the wiring |
| `flow refresh` | Run the curator / freshness re-derivation |
| `flow upgrade` | Update the engine assets without clobbering the instance |
| `flow version` | Print the engine version |

## Upgrade safety

`flow init` records the engine version in `.flow/VERSION`. `flow upgrade` replaces
only engine-owned files (playbook, steps, templates, commands, agents, hooks, check
modules) and never touches instance files (guardrails/always-on, config.yaml,
knowledge/map, knowledge-map.yaml, worklog). A manifest marks each shipped file as
`engine` or `instance`.
