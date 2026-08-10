# Flow — a governed AI-DLC methodology you can drop into any repo

[![PyPI](https://img.shields.io/pypi/v/flow-aidlc.svg)](https://pypi.org/project/flow-aidlc/)
[![Python versions](https://img.shields.io/pypi/pyversions/flow-aidlc.svg)](https://pypi.org/project/flow-aidlc/)
[![CI](https://github.com/dev-mian-zubair/flow-aidlc/actions/workflows/ci.yml/badge.svg)](https://github.com/dev-mian-zubair/flow-aidlc/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Flow turns "vibe coding with an AI agent" into a governed, auditable loop:
`Scope → Shape → Build → Ship`** — with mechanical **guardrails**, a committed
**code graph** as the source of truth for code structure, and **quality gates**
that run locally and in CI. The engine ships generic; one command scaffolds a
per-project instance you own.

```bash
pipx install flow-aidlc      # the `flow` CLI  (or: uv tool install flow-aidlc)
```

> 🌍 **Any language.** Flow is a Python-based CLI, but it governs a repo in *any*
> language — Python is only the CLI's own runtime (like `ruff` or `aws-cli`). You
> point it at *your* test/build commands; nothing about your codebase is assumed.

> 🧭 **One lifecycle, two modes.** **`controlled`** (default — a human approves each
> checkpoint) or **`auto`** (adversarial agent panels replace the human stop and it
> merges on green CI). Both run *every* gate.

---

## 📚 Contents

[How it works](#-how-it-works) · [Quick start](#-quick-start) · [The lifecycle](#-the-lifecycle) ·
[Slash commands](#️-slash-commands-in-claude-code) · [CLI reference](#️-cli-reference) ·
[Project layout](#-project-layout) · [Configuration](#️-configuration) ·
[Integrations](#-integrations) · [Prerequisites](#-prerequisites) ·
[Execution modes](#-execution-modes) · [Development](#-development)

---

## 🧭 How It Works

Flow governs an AI agent's work with three mechanical inputs, so "the agent did
something" becomes "the agent did the *approved* thing, provably":

```
                              your idea
                                  │
                                  ▼
   ┌──────────────────────────────────────────────────────────────┐
   │   SCOPE   →    SHAPE      →     BUILD       →      SHIP         │
   │  ticket      requirements    per slice:        whole-branch    │
   │  on your     → design        plan → TDD →       review →       │
   │  tracker     → slices        verify             open PR        │
   └──────────────────────────────────────────────────────────────┘
         ▲                 ▲                  ▲               ▲
         │                 │                  │               │
   ┌───────────┐   ┌───────────────┐   ┌─────────────┐  ┌────────────┐
   │ GUARDRAILS│   │  CODE GRAPH   │   │ QUALITY GATE│  │ CHECKPOINTS│
   │ your      │   │  who-calls /  │   │ flow check  │  │ human ✋ or  │
   │ invariants│   │  dependents / │   │ (local+CI)  │  │ agent panel │
   │ (blocking)│   │  impact (MCP) │   │             │  │             │
   └───────────┘   └───────────────┘   └─────────────┘  └────────────┘
```

- **Guardrails** — always-on, *blocking* invariant checks you author for your codebase. The Build/verify gate refuses to pass while one is violated.
- **Code graph** — structure (callers, dependents, contracts, impact) is extracted into a committed [Graphify](https://pypi.org/project/graphifyy/) graph and queried by agents over MCP, instead of hand-written docs that drift.
- **Quality gate** — `flow check` runs offline checks (guardrail-lint, structure, config-consistency) locally *and* in CI.
- **Checkpoints** — the lifecycle stops at each gate for a human `/flow-approve` (controlled) or an adversarial agent panel (auto).

---

## 🚀 Quick Start

### 1. Install the CLI

| Method | Command |
|---|---|
| **pipx** (recommended) | `pipx install flow-aidlc` |
| **uv** | `uv tool install flow-aidlc` |
| **pip** | `pip install flow-aidlc` |

### 2. Install the Claude Code prerequisites (once per machine)

```
/plugin install superpowers          # brainstorming, plan-writing, TDD, review   (required)
/plugin install pr-review-toolkit    # the whole-branch Ship review                (required)
uv tool install "graphifyy[mcp]"     # the code-graph backend, queried over MCP    (recommended)
```

`flow doctor` verifies all three and **warns** (never hard-fails) if one is missing.
See [Prerequisites](#-prerequisites) for what each does.

### 3. Scaffold Flow into your repo

```bash
cd your-repo
flow init                    # interactive — or pass flags to skip the prompts
```

### 4. Configure & verify

```bash
# set your toolchain in .flow/config.yaml → commands (test/build/lint), then:
flow setup      # install the graph tool, build the code graph, run flow doctor
flow check      # the offline quality gate → should print `gate PASSED`
```

### 5. Run your first feature — in Claude Code

```
/flow-scope "add a read-only endpoint listing departments over budget"
/flow-approve                # creates the ticket → e.g. TASK-42
/flow-start TASK-42          # Shape: requirements → design → slices (approve each)
/flow-slice                  # Build one slice (TDD); repeat until all slices done
/flow-ship                   # harden → retro → open the PR
```

---

## 🔄 The Lifecycle

One path, four phases, gated at each `checkpoint`. In **controlled** mode you clear
each checkpoint with `/flow-approve`; in **auto** mode an agent panel does.

```
 SCOPE ─────────────────────────────────────────────────────────────► ticket
   clarify → story → publish ✋                       (/flow-scope)

 SHAPE ─────────────────────────────────────────────────────────────► slices
   [map] → [research ✋] → requirements ✋ → design ✋ → slicing   (/flow-start <id>)
   └ map / research are conditional (brownfield / new dependency)

 BUILD  (per slice, repeat) ─────────────────────────────────────────► green code
   slice-design → code-plan ✋ → generate (TDD) → verify ✋       (/flow-slice)
   └ verify = guardrail-verifier + code review + checkpoint-reviewer

 SHIP ───────────────────────────────────────────────────────────────► open PR
   branch-hardening ✋ → learnings retro → open-pr ✋            (/flow-ship)
   └ controlled: stops at the open PR (your team owns the merge)
   └ auto: merges on green CI, then pulls the next ticket

 ✋ = checkpoint (human /flow-approve, or an agent panel in auto mode)
```

---

## ⌨️ Slash Commands (in Claude Code)

Drive the lifecycle from a Claude Code session in your initialized repo.

| Command | What it does | When |
|---|---|---|
| `/flow-scope "<idea>"` | Clarify intent, classify the ticket type, draft & (on approval) create the tracker ticket | start a new idea |
| `/flow-start <id>` | Open the Shape phase for a ticket: requirements → design → slices | after a ticket exists |
| `/flow-slice` | Run the next unstarted Build slice (plan → TDD → verify) | per slice, in Build |
| `/flow-ship` | Whole-branch review → learnings retro → open the PR | slices complete |
| `/flow-approve` | Clear the current checkpoint and advance | at every `✋` |
| `/flow-auto <id>` | Run the **whole lifecycle autonomously** — panels replace approvals, merge on green CI | hands-off delivery |
| `/flow-resume <id>` | Reconstruct state from the worklog and continue | after a break/compaction |
| `/flow-status <id>` | Show where a ticket sits in the pipeline | any time |
| `/flow-refresh` | Re-verify `knowledge/map/` invariants against current code | after big changes |
| `/flow-decide` | Record an architectural decision into `knowledge/decisions/` | ad-hoc |
| `/flow-changes` | Summarize the working-tree changes for the current task | any time |

---

## 🛠️ CLI Reference

The `flow` CLI scaffolds the instance and runs the gate. Every command searches
upward for a `.flow/` directory (override with `--path`).

### `flow init`
Scaffold the Flow instance into the current repo.
```bash
flow init [--tracker github] [--repo owner/name] [--id-prefix TASK] [--base origin/main] [-y]
```
| Option | Description |
|---|---|
| `--tracker` | `github` \| `jira` \| `linear` \| `azure-devops` \| `shortcut` \| `asana` \| `clickup` (default `github`) |
| `--repo` | tracker repo/project/team key (e.g. `owner/name`) |
| `--id-prefix` | ticket id prefix (default `TASK` → `TASK-42`) |
| `--base` | default base branch for feature branches + PR targets (default `origin/main`) |
| `--test-cmd` · `--build-cmd` · `--lint-cmd` · `--typecheck-cmd` | prefill `config.yaml → commands` |
| `-y, --yes` | accept defaults (non-interactive) · `--dry-run` · `--force` · `--path DIR` |

**Creates:** `.flow/` (engine + config), `.claude/` (commands/agents/hooks), `docs/flow/` (worklog + knowledge), `.mcp.json`, `.env.example`, `.gitignore` entries, and a `CLAUDE.md` pointer. Never touches your source.

### `flow setup`
One-command onboarding — detect `uv`, install the graph tool, run the configured `graph.build`, then `flow doctor`. Detect-and-guide: never hard-fails on a missing external tool.
```bash
flow setup [--with-impeccable]      # --with-impeccable also installs the Impeccable design skill
```

### `flow doctor`
Read-only health check: hooks installed, MCP reachable, structure valid, code graph wired, credentials resolve, auto-mode readiness.
```bash
flow doctor [--fix]                 # --fix applies safe mechanical fixes (e.g. chmod hook scripts)
```

### `flow check`
Run the quality gate — guardrail-lint, structure-check, reference-selfcheck, config-consistency. Runnable locally and in CI.
```bash
flow check [path]                   # exits non-zero on any failure; prints `gate PASSED` when clean
```

### `flow guardrail`
Author the blocking invariant checks for your codebase.
```bash
flow guardrail add <name>                 # scaffold a new always-on guardrail from the template
flow guardrail add <name> --optional      # register under guardrails.optional instead
flow guardrail add --from <pack>          # install a curated starter pack
flow guardrail packs                      # list available starter packs
```

### `flow map`
Scaffold a knowledge-map doc (subsystem invariants) and wire it into `knowledge-map.yaml`.
```bash
flow map add <glob> <doc> [--title "Human Title"]     # e.g. flow map add "src/**" core
```

### `flow ci`
Scaffold a CI workflow that runs the gate.
```bash
flow ci init [--gates semgrep,conftest,impeccable] [--force]
```
`--gates` adds deterministic gates beside the LLM guardrails: **semgrep** (SAST), **conftest** (OPA policy-as-code), **impeccable** (design quality).

### `flow status`
Show where each ticket sits in the `Scope → Shape → Build → Ship` pipeline (read from `docs/flow/worklog/`).
```bash
flow status
```

### `flow learnings`
Surface correction/redirection signals from task journals; `--promote` records them into `docs/flow/knowledge/practices.md`.
```bash
flow learnings [--promote]
```

### `flow secrets`
Route MCP credentials through a secrets manager (zero plaintext in the repo).
```bash
flow secrets use infisical      # or: doppler
flow secrets status             # report credential wiring per server
flow secrets off                # unwrap all wrapped servers
```

### `flow refresh`
Rebuild the code graph (structure freshness). `/flow-refresh` curates map *invariants*.
```bash
flow refresh [--dry-run]
```

### `flow upgrade`
Update engine assets **without touching your instance** (config, guardrails, knowledge maps, worklog are preserved — a manifest marks each shipped file `engine` or `instance`).
```bash
flow upgrade [--dry-run] [--force]
```

### `flow plugin build`
Regenerate the Claude Code plugin tree from the engine (single source of truth: `engine/claude/`).
```bash
flow plugin build [--out DIR]
```

### `flow version`
Print the engine version.

> `flow selftest` also exists — a maintainer command that runs the engine's own
> vendored unit suite from a source checkout (not an installed package).

---

## 📁 Project Layout

After `flow init`, your repo gains:

```
your-repo/
├── .flow/                    # the engine + your instance config (hidden machinery)
│   ├── playbook.md           #   the Scope→Shape→Build→Ship state machine
│   ├── config.yaml           #   YOUR config: commands, tracker, guardrails, graph, execution
│   ├── steps/  templates/    #   stage guides + artifact templates (engine)
│   ├── guardrails/           #   always-on/ (you author) + optional/ (engine starters)
│   └── knowledge-map.yaml    #   maps subsystem docs → the code they derive from
├── .claude/                  # Claude Code surface (required at repo root)
│   ├── commands/ agents/ hooks/
│   └── settings.json
├── .mcp.json                 # MCP server wiring (only ${VAR} references — no secrets)
└── docs/flow/                # human-facing artifacts
    ├── knowledge/
    │   ├── map/              #   subsystem invariants (curated)
    │   ├── decisions/        #   architectural decision records
    │   └── practices.md      #   promoted learnings
    └── worklog/              #   per-ticket run history (progress, journal, artifacts)
```

> `.flow/` is the hidden machinery; **`docs/flow/`** holds the human-facing worklog
> and knowledge. `.claude/` and `.mcp.json` stay at the repo root (Claude Code requires it).

---

## ⚙️ Configuration

`flow init` renders `.flow/config.yaml` — the single place that drives the engine:

```yaml
worklog:
  committed: true                    # worklog is committed history
commands:                            # YOUR toolchain — Flow's TDD runs `test`
  test:      "pytest"                # e.g. npm test | go test ./... | make test
  build:     "make build"
  lint:      "ruff check"
  typecheck: "mypy"
vcs:
  base: "origin/main"                # default base branch for feature branches + PRs
tracker:
  platform: "github"                 # github|jira|linear|azure-devops|shortcut|asana|clickup
  repo: "owner/name"
  id_scheme: "TASK-{n}"              # → worklog dir docs/flow/worklog/TASK-<n>-<slug>
  create:
    required_labels: [type, priority, area]
    ticket_types:   [bug, feat, task, epic]
guardrails:
  always_on: []                      # your blocking invariants (empty until you add them)
  optional:  [security-baseline, resiliency-baseline, test-coverage, dependency-provenance]
graph:
  backend: graphify                  # code-graph backend (queried over MCP)
  build: "graphify extract . --code-only --no-cluster --force"
  output: graphify-out/graph.json    # committed; only graph.json is tracked
execution:                           # defaults for /flow-auto (auto mode)
  label: flow-auto                   # tracker label that queues a ticket
  max_tasks: 5                       # hard cap per /flow-auto run
  review: { panel_size: 3, max_rounds: 5 }
  merge:  { gate: green-ci }
```

---

## 🔌 Integrations

### Issue trackers
Scope publishes tickets and Ship opens PRs through a **tracker adapter** that maps
Flow's universal operations (`CREATE_TICKET`, `ADD_SUB_ISSUE`, `OPEN_PR`, …) to a
platform. No step or agent names a platform-specific tool.

| Platform | Status | `tracker.repo` |
|---|---|---|
| **GitHub Issues** | ✅ default | `owner/name` |
| **Jira** | ✅ | project key |
| **Linear** | ✅ | team key |
| **Azure DevOps** | ✅ | `<org>/<project>` |
| **Shortcut** | ✅ | workspace-scoped |
| **Asana** | ✅ | project gid |
| **ClickUp** | ✅ | list id |

Switch with `flow init --tracker <platform>` (or edit `config.yaml`). See
[`INTEGRATIONS.md`](src/flow_aidlc/engine/flow/INTEGRATIONS.md).

### Secrets · Code graph · Design quality
- **Secrets** — `.mcp.json` holds only `${VAR}` references; supply them via a manager (`flow secrets use infisical`/`doppler`), a provider CLI (`gh auth token`), or a gitignored `.env`.
- **Code graph** — [Graphify](https://pypi.org/project/graphifyy/) over MCP answers who-calls / dependents / impact deterministically; without it, structural steps degrade to a read-only Explore/grep fallback.
- **Design quality (optional, UI)** — `flow setup --with-impeccable` installs [Impeccable](https://impeccable.style/) (Apache-2.0); Flow grounds UI work in its `PRODUCT.md`/`DESIGN.md` and `flow ci init --gates impeccable` gates it in CI.

---

## ✅ Prerequisites

Installed in your **Claude Code environment** (shared across projects), not by
`flow init`. `flow doctor` checks all three.

| Prereq | Install | Why |
|---|---|---|
| **[superpowers](https://github.com/obra/superpowers)** *(required)* | `/plugin install superpowers` | brainstorming, plan-writing, TDD, and review — invoked across the playbook |
| **pr-review-toolkit** *(required)* | `/plugin install pr-review-toolkit` | the whole-branch review at Ship/branch-hardening |
| **[Graphify](https://pypi.org/project/graphifyy/)** *(recommended)* | `uv tool install "graphifyy[mcp]"` | the code graph (who-calls / dependents / impact) over MCP |

---

## 🧩 Execution Modes

Same lifecycle, same gates — what differs is **who holds the gate**.

| | **`controlled`** (default) | **`auto`** (`/flow-auto`) |
|---|---|---|
| Checkpoints | human `/flow-approve` | adversarial agent panels (reuse `pr-review-toolkit` + `guardrail-verifier`) |
| Terminates at | the **open PR** (team owns the merge) | **merge on green CI**, then pulls the next `flow-auto`-labeled ticket |
| Human role | in-the-loop operator | on-the-loop policy-setter (labels the queue, authors invariants, owns branch protection) |

**Auto runs every gate `controlled` runs** — it removes the human *stop*, not the
*governance*. Runaway-safe: two-gate merge (panels **and** green CI), branch
protection never bypassed, **park-on-fail** (a stuck task becomes a draft PR +
`flow-blocked`), a `.flow/STOP` kill-switch, and a `max_tasks` cap.

---

## 🏗️ The Two Layers

| Engine (shipped, generic) | Instance (generated by `flow init`, yours) |
|---|---|
| playbook, step guides, templates | `config.yaml` (tracker, id-scheme, commands) |
| commands, agents, hooks | `guardrails/always-on/*` — your invariants |
| the `flow` CLI + check modules | `docs/flow/knowledge/map/*` — your subsystem invariants |
| guardrail/config/map **templates** | `config.yaml → graph:` + the committed code graph |

Flow also ships as an installable **Claude Code plugin** (`/plugin install flow`)
that surfaces the `/flow-*` commands and calls the same CLI. See
[`ARCHITECTURE.md`](ARCHITECTURE.md) for the full model.

---

## 👩‍💻 Development

```bash
git clone https://github.com/dev-mian-zubair/flow-aidlc.git
cd flow-aidlc
uv run pre-commit install                          # enable the git hooks (once)
uv run --extra dev pytest -q                        # run the test suite
```

Contributions welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md) (setup, the two
repo invariants, commit conventions, and the release flow).

## 📄 License

MIT — see [`LICENSE`](LICENSE).

## 🔗 Links

- **PyPI:** https://pypi.org/project/flow-aidlc/
- **Source:** https://github.com/dev-mian-zubair/flow-aidlc
- **Architecture:** [`ARCHITECTURE.md`](ARCHITECTURE.md) · **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md) · **Publishing:** [`docs/PUBLISHING.md`](docs/PUBLISHING.md)
