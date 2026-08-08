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

- `config.yaml` drives which guardrails are active, the tracker/id-scheme, the
  `graph:` block (backend, MCP, build command, focus dirs), and `vcs.base` — the
  default base branch for feature branches and PR targets (per-task override: the
  `Base branch:` line in a worklog's `progress.md`).
- `knowledge-map.yaml` indexes subsystem → owning invariant doc; **code structure**
  itself lives in the committed code graph, not in prose.
- The templates drive every worklog artifact (`cp` template → fill).

Nothing project-specific is hardcoded in logic, so packaging is "move the
project data out, ship the engine, let `init` regenerate the data."

## Structure comes from the code graph (not prose)

Flow does not maintain code *structure* — callers, dependents, contracts, the
subsystem surface — as hand-written docs that drift. Structure is extracted into a
committed **code graph** ([Graphify](https://pypi.org/project/graphifyy/), ADR
0008/0009) and queried by agents over MCP through a backend-neutral adapter
(`.flow/steps/shared/graph.md`, universal ops `WHO_CALLS` / `NEIGHBORS` / `HUBS` /
`IMPACT_OF_DIFF`). Consequences:

- **Graphify is a prerequisite** (alongside superpowers). Install
  `uv tool install "graphifyy[mcp]"`; the graph is built by the configured
  `config.yaml → graph.build` and committed (`graphify-out/graph.json`). If it is
  absent, structural steps fall back to a read-only `Explore`/grep survey.
- **The curated `knowledge/map/` docs hold only invariants** — the load-bearing rules
  a graph can't know — each stamped `enforced-by: <guardrail>`. There is **no
  doc-freshness loop**: structure can't go stale (it's re-derived from the graph), and
  invariants are held by their guardrail at Build/verify, not by a stale flag.
- **`flow check` config-consistency** enforces the graph is wired: `graph.backend` must
  be implemented in the adapter (C6) and `graph.root` / `graph.focus` / `graph.ignore_file`
  must resolve on disk (C7).

## Two execution modes

Flow runs one lifecycle (Scope→Shape→Build→Ship) in two modes. The stages, artifacts,
guardrails, and gates are identical across modes — the difference is **who enforces the
gate**.

- **`controlled` (default):** a human `/flow-approve`s each `checkpoint: yes` stage;
  Ship is terminal at the open PR (below). Human-in-the-loop AI-DLC.
- **`auto` (`/flow-auto` only):** the human checkpoints are replaced by **stage-typed
  adversarial reviewer panels** (reusing `pr-review-toolkit` + `guardrail-verifier`) that
  fix-loop to consensus or park; Ship extends past open-PR to **merge on green CI**, then
  the loop pulls the next `flow-auto`-labeled ticket. On-the-loop autonomous AI-DLC.

The load-bearing invariant: **auto runs every gate `controlled` runs** — it removes the
human *stop*, not the *governance*. Enforcement moves from human judgment to agent panels
+ deterministic CI; the human moves from per-step approver to **policy author** (the
guardrails, the `flow-auto` label as the work queue, branch protection). Safety rails:
two-gate merge (panels + green CI), branch protection never bypassed, park-on-fail,
`.flow/STOP` kill-switch, `max_tasks` cap, and a CI-required precondition. There is no
global mode toggle — `auto` happens only via `/flow-auto`. Config defaults live under
`config.yaml → execution:`.

## Ship ends at the open PR (controlled) / merges on green CI (auto)

In **`controlled`** mode the Ship phase is **terminal at the open PR** (branch-hardening →
learnings → open-pr, ADR 0010): Flow produces a reviewed, PR-ready branch and stops.
Merge, required checks, approvals, ticket close, and any serialization-lock release are
owned by the team on the host — branch protection on `vcs.base` is authoritative.

In **`auto`** mode Ship continues past open-pr: it polls the PR's required checks and
**merges only on green CI** (respecting branch protection), then the autonomous loop
proceeds to the next ticket. The team's control surface shifts from *approving each PR*
to *setting policy* (branch protection + the CI gates + the `flow-auto` label).

## Distribution

Two complementary channels, same engine:

1. **pip / pipx CLI** (`flow`) — install anywhere, scaffold + gate in CI. Primary.
2. **Claude Code plugin** — the `.claude/{commands,agents,hooks}` assets map
   natively onto the plugin format; the plugin surfaces `/flow-*` and calls the
   same CLI for scaffolding. (Layered on after the CLI.)

## The command surface

| Command | Purpose |
|---|---|
| `flow init` | Scaffold the instance into the current repo (interactive; `--base` sets `vcs.base`) |
| `flow setup` | One-command onboarding — detect `uv` + install the graph tool, run `graph.build`, then `flow doctor` (detect-and-guide; never fails hard on a missing tool) |
| `flow guardrail add <name>` | Scaffold a new always-on guardrail from the template + register it |
| `flow map add <glob> <doc>` | Scaffold a knowledge/map doc + wire knowledge-map.yaml |
| `flow doctor` | Health check — hooks installed, MCP reachable, structure valid, code graph wired |
| `flow check` | Run the quality gate (guardrail-lint, structure, reference-selfcheck, config-consistency) |
| `flow selftest` | Mechanical offline self-test of the wiring |
| `flow refresh` | Rebuild the code graph (structure freshness); `/flow-refresh` curates map invariants |
| `flow upgrade` | Update the engine assets without clobbering the instance |
| `flow version` | Print the engine version |

## Upgrade safety

`flow init` records the engine version in `.flow/VERSION`. `flow upgrade` replaces
only engine-owned files (playbook, steps, templates, commands, agents, hooks, check
modules) and never touches instance files (guardrails/always-on, config.yaml,
knowledge/map, knowledge-map.yaml, worklog). A manifest marks each shipped file as
`engine` or `instance`.
