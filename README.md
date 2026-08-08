# Flow — a governed AI-DLC methodology you can drop into any repo

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

## Prerequisites

These are installed in your **Claude Code environment** (or, for Graphify, your
machine), not by `flow init` — the scaffolder is repo-local, while these are
shared across projects. `flow doctor` verifies all three are present and warns if
one is missing, so a `/flow-*` run never fails mid-stage on an absent dependency.

- **[superpowers](https://github.com/obra/superpowers) skills** *(required)* — Flow
  delegates brainstorming, plan-writing, TDD, and code review to the `superpowers`
  skill ecosystem; it is invoked at nearly every stage of the playbook. Install in
  Claude Code: `/plugin install superpowers`.
- **`pr-review-toolkit` agents** *(required)* — the Ship/branch-hardening gate runs
  a whole-branch review through these specialized agents (code review, silent-failure
  hunting, test analysis, type-design, comments) before opening a PR. Install in
  Claude Code: `/plugin install pr-review-toolkit`.
- **[Graphify](https://pypi.org/project/graphifyy/)** *(recommended)* — Flow's source
  of truth for code *structure*. Structure is not maintained as prose; it is extracted
  into a committed **code graph** that agents query over MCP. Install with
  `uv tool install "graphifyy[mcp]"` (the `[mcp]` extra powers the agent-facing
  `graphify` MCP server; the base package alone builds the graph for CI). Without it,
  the structural steps degrade to a read-only `Explore`/grep fallback — nothing breaks,
  but caller/dependent resolution is no longer deterministic.

## Quickstart

```bash
pipx install flow-aidlc          # or: pip install flow-aidlc
uv tool install "graphifyy[mcp]" # the code-graph backend (structure source of truth)
cd your-repo
flow init                        # scaffold .flow/, .claude/, knowledge/, git hooks (--base sets vcs.base)
flow setup                       # one-command onboarding: graph tool + graph build + flow doctor
flow check                       # run the quality gate
```

`flow init --base <branch>` sets `config.yaml → vcs.base` — the default base branch
for feature branches and PR targets (per-task override: the `Base branch:` line in a
worklog's `progress.md`). `flow setup` is the portable onboarding chain: it detects
`uv` and installs the graph tool, runs the configured `graph.build`, and finishes with
`flow doctor` — never failing hard on a missing external tool.

Then, in Claude Code:

```
/flow-scope "add a read-only endpoint listing departments over budget"
/flow-shape        # requirements → design → slices (gated)
/flow-build        # per-slice: plan → generate (TDD) → verify (guardrails)
/flow-ship         # branch-hardening → learnings retro → open-pr (terminal; the team owns the merge)
```

## What you get

- **The state machine** (`.flow/playbook.md`) — Scope → Shape → Build → Ship, gated at each checkpoint.
- **Mechanical enforcement** — Claude Code hooks that journal prompts, guard scope, and hold checkpoints.
- **Guardrails** — always-on, blocking invariant checks you author for *your* codebase (the engine ships the mechanism + templates; `flow guardrail add` scaffolds one, or `flow guardrail add --from <pack>` installs a curated starter pack — see `flow guardrail packs`).
- **Code graph as structure source of truth** — a committed [Graphify](https://pypi.org/project/graphifyy/) graph, queried over MCP, answers "who calls this / what depends on it / what's the contract" deterministically. Curated `knowledge/map/` docs hold only the **invariants** a graph can't know; each is enforced by a guardrail, so structure can't go stale.
- **Quality gate** — `flow check` (guardrail-lint, structure-check, reference-selfcheck, config-consistency incl. graph-backend + graph-paths) — runnable locally and in CI.
- **Superpowers-powered** — delegates brainstorming, plan-writing, TDD, and code review to the `superpowers` skill ecosystem.
- **Pluggable issue tracker** — Scope publishes tickets and Ship opens the PR through a tracker adapter (`steps/shared/tracker.md`) that maps Flow's universal operations (`CREATE_TICKET`, `ADD_SUB_ISSUE`, `OPEN_PR`, …) to a platform. No step or agent names a platform-specific tool, and the `config-consistency` gate (C3) refuses an unimplemented platform.
- **Secrets, not in the repo** — `.mcp.json` holds only `${VAR}` references; supply values via a secrets manager (`flow secrets use infisical`/`doppler` — zero plaintext), a provider CLI (`gh auth token`), or a gitignored `.env`. `flow doctor` verifies they resolve.
- **Observability** — `flow status` shows where each ticket sits in Scope→Shape→Build→Ship (read from `worklog/`); `flow learnings` surfaces correction/redirection signals from task journals and `--promote`s them into `knowledge/practices.md`. `flow ci init` scaffolds a workflow that runs the gate in CI (`--gates semgrep,conftest` adds deterministic SAST + policy-as-code gates beside the LLM guardrails).
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
| the `flow` CLI + check modules | `knowledge/map/*` — your subsystem invariants |
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

## License

MIT
