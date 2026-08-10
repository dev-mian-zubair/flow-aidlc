# Flow — a governed AI-DLC methodology you can drop into any repo

[![PyPI](https://img.shields.io/pypi/v/flow-aidlc.svg)](https://pypi.org/project/flow-aidlc/)
[![Python versions](https://img.shields.io/pypi/pyversions/flow-aidlc.svg)](https://pypi.org/project/flow-aidlc/)
[![CI](https://github.com/dev-mian-zubair/flow-aidlc/actions/workflows/ci.yml/badge.svg)](https://github.com/dev-mian-zubair/flow-aidlc/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Flow** turns "vibe coding with an AI agent" into a governed, auditable development
loop: **Scope → Shape → Build → Ship**, with mechanical guardrails, a committed
**code graph** as the source of truth for code structure, and quality gates that run
in CI. It is **project-agnostic** — the engine ships generic; a one-command
`flow init` scaffolds a per-project instance, and each project authors its own
invariants (guardrails), subsystem maps, and tracker config.

It runs in **two modes over the same lifecycle**: **supervised** (`controlled`, the
default — a human approves each checkpoint; terminates at the open PR) and
**autonomous** (`auto`, via `/flow-auto` — adversarial agent panels replace the human
stop, the PR merges on green CI, and the loop grinds the next ticket). Both run
*every* gate; auto only changes *who holds the gate* — from a human to agent panels +
deterministic CI. See [Execution modes](#execution-modes).

> Flow is a reusable, project-agnostic engine + a CLI to install it into any repo.

---

## Setup

Flow is a Python-based CLI, but it governs a repo in **any language** — Python is
just the CLI's own runtime (like `ruff` or `aws-cli`). You point Flow at your
project's own test/build commands; nothing about your codebase is assumed.

### 1. Install the CLI

```bash
pipx install flow-aidlc      # recommended (isolated) — or: uv tool install flow-aidlc
flow version
```

### 2. Install the Claude Code prerequisites (once per machine, not per repo)

Flow delegates process work to two Claude Code plugins and queries a code graph.
`flow doctor` checks all three and **warns** (never fails a run) if one is missing.

| Prereq | Install in Claude Code | Why |
|---|---|---|
| **superpowers** *(required)* | `/plugin install superpowers` | brainstorming, plan-writing, TDD, review — invoked all over the playbook |
| **pr-review-toolkit** *(required)* | `/plugin install pr-review-toolkit` | the whole-branch review at Ship/branch-hardening |
| **[Graphify](https://pypi.org/project/graphifyy/)** *(recommended)* | `uv tool install "graphifyy[mcp]"` | the code graph (who-calls / dependents / impact), queried over MCP |

Without Graphify the structural steps degrade to a read-only `Explore`/grep
fallback — nothing breaks, but caller/dependent resolution is no longer deterministic.

### 3. Scaffold Flow into your repo

```bash
cd your-repo
flow init                    # interactive; or pass flags (below) to skip the prompts
```

`flow init` creates the following and **never touches your source**:

- **`.flow/`** — the engine + your `config.yaml`, guardrails, and knowledge-map
- **`.claude/`** — the `/flow-*` commands, phase agents, and governance hooks
- **`docs/flow/`** — `worklog/` (per-ticket run history) + `knowledge/` (invariants, decisions)
- **`.mcp.json`**, **`.env.example`**, `.gitignore` entries, and a `CLAUDE.md` pointer

Flags: `--tracker <github|jira|linear|azure-devops|shortcut|asana|clickup>` (default `github`),
`--base <branch>` (default base for feature branches + PR targets),
`--id-prefix <PREFIX>` (ticket id prefix, default `TASK`), `--yes` (accept defaults).

### 4. Configure the instance

- **Test / build commands** — set `.flow/config.yaml → commands` (`test`, `build`,
  `lint`, `typecheck`) to your toolchain: `pytest`, `npm test`, `go test ./...`,
  `make test`, … Flow's TDD stage runs *your* `test` command.
- **Tracker credentials** — `.mcp.json` holds only `${VAR}` references. Supply them by
  copying `.env.example` → `.env` (gitignored) and filling in, **or** a secrets manager
  (`flow secrets use infisical` / `doppler`), **or** a provider CLI (`gh auth token`).

### 5. Build the graph and verify

```bash
flow setup      # detect uv, install the graph tool, build the code graph, then run flow doctor
flow doctor     # health-check: hooks installed, MCP reachable, graph wired, credentials resolve
flow check      # the offline quality gate (guardrail-lint, structure, config-consistency)
```

`flow check` should end with **`gate PASSED`**. You're ready to run the lifecycle.

## Quickstart: your first feature

Everything below runs **inside a Claude Code session** in your initialized repo.
Flow drives one lifecycle — **Scope → Shape → Build → Ship** — and stops at each
checkpoint for your `/flow-approve` (in the default `controlled` mode).

```
# 1. SCOPE — turn an idea into a tracker ticket
/flow-scope "add a read-only endpoint listing departments over budget"
#   clarifies intent → proposes a ticket type → drafts the ticket
#   → /flow-approve   (creates the ticket; returns an id, e.g. TASK-42)

# 2. SHAPE — requirements → design → slices, from the ticket id
/flow-start TASK-42
#   (brownfield: maps the touched code first) → requirements → design → slices
#   → /flow-approve at each checkpoint (research, requirements, design)

# 3. BUILD — one slice at a time, test-first
/flow-slice
#   slice-design → code-plan → /flow-approve → generate (TDD) → verify (guardrails) → /flow-approve
#   repeat /flow-slice until every slice is complete

# 4. SHIP — harden, retro, open the PR
/flow-ship
#   whole-branch review → learnings retro → /flow-approve → opens the PR
#   Flow stops at the open PR; your team owns the merge.
```

Handy any time: **`/flow-status <id>`** (where a ticket sits in the pipeline),
**`/flow-resume <id>`** (pick up after a break), **`/flow-approve`** (clear the
current checkpoint).

**Autonomous mode:** **`/flow-auto <id>`** runs the same lifecycle with **no human
stops** — adversarial agent panels replace your approvals and it merges on green CI.
See [Execution modes](#execution-modes).

## What you get

- **The state machine** (`.flow/playbook.md`) — Scope → Shape → Build → Ship, gated at each checkpoint.
- **Mechanical enforcement** — Claude Code hooks that journal prompts, guard scope, and hold checkpoints.
- **Guardrails** — always-on, blocking invariant checks you author for *your* codebase (the engine ships the mechanism + templates; `flow guardrail add` scaffolds one, or `flow guardrail add --from <pack>` installs a curated starter pack — see `flow guardrail packs`).
- **Code graph as structure source of truth** — a committed [Graphify](https://pypi.org/project/graphifyy/) graph, queried over MCP, answers "who calls this / what depends on it / what's the contract" deterministically. Curated `docs/flow/knowledge/map/` docs hold only the **invariants** a graph can't know; each is enforced by a guardrail, so structure can't go stale.
- **Quality gate** — `flow check` (guardrail-lint, structure-check, reference-selfcheck, config-consistency incl. graph-backend + graph-paths) — runnable locally and in CI.
- **Superpowers-powered** — delegates brainstorming, plan-writing, TDD, and code review to the `superpowers` skill ecosystem.
- **Pluggable issue tracker** — Scope publishes tickets and Ship opens the PR through a tracker adapter (`steps/shared/tracker.md`) that maps Flow's universal operations (`CREATE_TICKET`, `ADD_SUB_ISSUE`, `OPEN_PR`, …) to a platform. No step or agent names a platform-specific tool, and the `config-consistency` gate (C3) refuses an unimplemented platform.
- **Secrets, not in the repo** — `.mcp.json` holds only `${VAR}` references; supply values via a secrets manager (`flow secrets use infisical`/`doppler` — zero plaintext), a provider CLI (`gh auth token`), or a gitignored `.env`. `flow doctor` verifies they resolve.
- **Observability** — `flow status` shows where each ticket sits in Scope→Shape→Build→Ship (read from `docs/flow/worklog/`); `flow learnings` surfaces correction/redirection signals from task journals and `--promote`s them into `docs/flow/knowledge/practices.md`. `flow ci init` scaffolds a workflow that runs the gate in CI (`--gates semgrep,conftest` adds deterministic SAST + policy-as-code gates beside the LLM guardrails).
- **Design quality (optional, UI)** — `flow setup --with-impeccable` installs [Impeccable](https://impeccable.style/) (Apache-2.0); Flow reads its `PRODUCT.md`/`DESIGN.md` for grounding, generates/validates UI against them, and `flow ci init --gates impeccable` gates design quality in CI.
- **Two execution modes** — the same lifecycle, supervised **or** autonomous (see below).

## Execution modes

Flow runs **one lifecycle** (Scope→Shape→Build→Ship) in either of two modes. The
stages, artifacts, guardrails, and gates are identical — what differs is **who holds
the gate**.

| | **`controlled`** (default) | **`auto`** (`/flow-auto`) |
|---|---|---|
| Checkpoints | human `/flow-approve` at each gate | **adversarial agent panels** replace the human stop (reuse `pr-review-toolkit` + `guardrail-verifier`; loop until consensus or park) |
| Terminates at | the **open PR** (the team owns the merge) | **merge on green CI**, then the loop pulls the next `flow-auto`-labeled ticket |
| Human role | in-the-loop operator (approves each step) | on-the-loop policy-setter (labels the queue, authors the invariants, owns branch protection) |
| Governance | human judgment per checkpoint | agent panels **+** deterministic CI + branch protection |

**Auto runs every gate `controlled` runs** — it never trades a gate for speed. It's
runaway-safe: a two-gate merge (panels **and** green CI), branch protection never
bypassed, **park-on-fail** (a stuck task becomes a draft PR + `flow-blocked` and the
loop continues), a `.flow/STOP` kill-switch, a `max_tasks` cap, and a hard precondition
that CI exists. Auto is entered only via `/flow-auto` — there is no global toggle.

> This is why Flow is still a **governed AI-DLC** in both modes: the governance
> *structure* is unchanged; auto only moves the *enforcement* from a human to agent
> panels + CI, and the human from per-step approver to policy author.

## Supported trackers

| Platform | Status | MCP server | Notes |
|---|---|---|---|
| **GitHub Issues** | ✅ Implemented (default) | `@modelcontextprotocol/server-github` | `tracker.repo` = `owner/name`; `OPEN_PR` native |
| **Jira** | ✅ Implemented | `mcp-atlassian` (sooperset) | `tracker.repo` = the **project key**; site URL via `JIRA_URL`; `OPEN_PR` runs on your VCS with the Jira key in the PR |
| **Linear** | ✅ Implemented | Linear MCP (`LINEAR_API_KEY`) | `tracker.repo` = the **team key**; type via labels (no native issue type); `OPEN_PR` runs on your VCS with the Linear id in the branch/PR |
| **Azure DevOps** | ✅ Implemented | `microsoft/azure-devops-mcp` (first-party) | `tracker.repo` = `<org>/<project>`; native work-item types; `OPEN_PR` native on Azure Repos (else your VCS) |
| **Shortcut** | ✅ Implemented | `useshortcut/mcp-server-shortcut` (official) | workspace-scoped (`tracker.repo` unused); native story type + epics; `OPEN_PR` on your VCS |
| **Asana** | ✅ Implemented | `roychri/mcp-server-asana` (community) | `tracker.repo` = project gid; type via tags; `OPEN_PR` on your VCS |
| **ClickUp** | ✅ Implemented | `clickup-mcp` (community) | `tracker.repo` = list id; custom task types; `OPEN_PR` on your VCS |

Switch trackers via `flow init --tracker <platform>` (or edit `config.yaml`) — see [`INTEGRATIONS.md`](src/flow_aidlc/engine/flow/INTEGRATIONS.md). Adapter tool names track each platform's MCP server and may vary by version.

## The two layers

| Engine (shipped, generic) | Instance (generated by `flow init`, yours) |
|---|---|
| playbook, step guides, templates | `config.yaml` (tracker, id-scheme) |
| commands, agents, hooks | `guardrails/always-on/*` — your invariants |
| the `flow` CLI + check modules | `docs/flow/knowledge/map/*` — your subsystem invariants |
| guardrail/config/map **templates** | `config.yaml → graph:` + the committed code graph |

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full model.

## Claude Code plugin

Flow's Claude Code surface — the `/flow-*` commands, the phase agents, and the
governance hooks — also ships as an installable **Claude Code plugin** under
[`plugin/`](plugin/). It composes with the CLI:

- the **plugin** provides the Claude Code surface (`/plugin install flow`);
- the **`flow` CLI** provides the per-project scaffolding (`flow init`) and the
  gate (`flow check`).

Install the plugin **and** run `flow init` — the hooks and commands operate on
the `.flow/` instance that `flow init` creates. See [`plugin/README.md`](plugin/README.md)
for the install flow. `plugin/` is a build artifact regenerated from the engine
by `flow plugin build` (single source of truth: `src/flow_aidlc/engine/claude/`).

## Status

**Canonical source of truth for the Flow engine.** The engine and CLI are
feature-complete; we are in the polish phase.

## Development

```bash
uv run --with pytest --with pyyaml python -m pytest -q   # run the suite
uv run pre-commit install                                # enable the git hooks (once)
```

The pre-commit hooks run a **version-drift guard** (`scripts/bump_version.py
--check` — keeps `pyproject.toml`, `__version__`, and the engine `VERSION` in
lockstep) plus basic hygiene. Releases are cut by pushing a `v*` tag; see
[`docs/PUBLISHING.md`](docs/PUBLISHING.md).

## License

MIT
