# Flow — Start Here

Flow is a governed, checkpoint-gated development process for this repo. Every task
moves through four phases — **Scope → Shape → Build → Ship** — with explicit approval
gates between them. At each gate a human (or an authorized agent) runs `/flow-approve`
before work continues. The authoritative rules and the per-stage guide-loading table
live in [playbook.md](playbook.md).

---

## Prerequisites

Before starting a Flow session, confirm the following:

1. **Flow installed** — `.flow/`, `.claude/hooks/`, and `.claude/commands/` are all
   present in the repo (they are committed).
2. **A tracker ticket** — you need a ticket id in your configured id-scheme
   (`config.yaml` → `tracker.id_scheme`). Run `/flow-scope` with a one-line idea if
   you do not have one yet.
3. **A sentence of intent** — what change do you want to make and why?
4. **A branch** — Shape entry (`/flow-start`) creates the feature branch off the
   configured base (`config.yaml` → `vcs.base`); see `steps/shared/kickoff.md`.
5. **Integrations healthy** — for a new machine, run the one-command onboarding:
   ```
   flow setup
   ```
   It installs the code-graph tool, builds the graph, and runs `flow doctor` (config
   files, MCP env vars + commands, hook permissions, the code graph). See
   [`INTEGRATIONS.md`](INTEGRATIONS.md) for the manual steps and env vars.

---

## Command Surface

### 5 Core commands

| Command | What it does |
|---------|-------------|
| `/flow-start <ID>-NNN` | Scaffold the worklog and enter the Shape phase |
| `/flow-resume <ID>-NNN` | Rebuild state after a context reset and continue |
| `/flow-approve` | Approve the current checkpoint and advance to the next stage |
| `/flow-status <ID>-NNN` | Print progress, open questions, and stale-doc flags |
| `/flow-slice [name]` | Manually start the next Build slice |

### 5 Override commands

| Command | What it does |
|---------|-------------|
| `/flow-scope <idea>` | Run the Scope front door (clarify → story → publish) |
| `/flow-ship` | Enter the Ship phase (branch-hardening → learnings → open-pr). Terminal at the open PR; the team owns the merge |
| `/flow-changes <desc>` | Record a change request at the current checkpoint |
| `/flow-decide <title>` | Graduate a cross-cutting decision to `knowledge/decisions/` |
| `/flow-refresh` | Dispatch the curator to verify `knowledge/map/` invariants against current code |

---

## Phase Flow

```
Scope ──────► Shape ──────────────► Build (per slice) ──► Ship
  clarify       map-existing*         slice-design          branch-hardening [✓]
  story         requirements [✓]      code-plan [✓]         learnings
  publish [✓]   design [✓]            generate              open-pr [✓]
                slicing               verify [✓]
```

`[✓]` = checkpoint — stop here and wait for `/flow-approve`.  
Ship is **terminal at the open PR** — the team owns the merge, required checks, and ticket close.  
`*` = conditional on brownfield work (existing code being modified).

- **Scope** (`.flow/steps/scope/`) — turn an idea into a tracker ticket.
  Invokes `superpowers:brainstorming`.
- **Shape** (`.flow/steps/shape/`) — decide *what* to build before touching
  code: map existing surface, write requirements, design the solution, cut
  slices. Invokes `superpowers:brainstorming`.
- **Build** (`.flow/steps/build/`) — implement one slice at a time, test-first.
  Invokes `superpowers:test-driven-development` (generate) and
  `superpowers:requesting-code-review` + `superpowers:verification-before-completion`
  (verify).
- **Ship** (`.flow/steps/ship/`) — harden the full branch, run the pre-PR learnings
  retro, then open the PR and stop. Invokes `superpowers:finishing-a-development-branch`.

---

## Where Things Live

| Path | Contents |
|------|----------|
| `.flow/` | Playbook, config, step guides, templates, guardrails |
| `.flow/playbook.md` | The canonical state machine — read this first |
| `.flow/config.yaml` | Guardrail toggles, tracker config, `vcs.base` |
| `.flow/steps/<phase>/` | Step guide files loaded on demand per stage |
| `.flow/guardrails/` | Always-on and optional guardrail rule docs |
| `.claude/commands/` | Slash-command definitions (`/flow-*`) |
| `.claude/agents/` | Subagent definitions (build, shape, review, etc.) |
| `.claude/hooks/` | Claude Code lifecycle hooks (prompt-journal, scope-guard, etc.) |
| `knowledge/` | Persistent codebase knowledge: `map/` (invariants) and `decisions/` |
| `worklog/<ID>-NNN/` | Per-task artifacts: `progress.md`, `journal.md`, `shape/`, `build/`, `ship/` |

The quality gate runs as `flow check` (offline self-test: `flow selftest`).

---

## Powered by Superpowers

Each phase delegates to the matching skill at the right moment — you do not
invoke these manually; the step guides load them:

| Phase/Stage | Skill invoked |
|-------------|---------------|
| Scope/clarify, Shape/requirements | `superpowers:brainstorming` |
| Build/generate | `superpowers:test-driven-development` |
| Build/verify | `superpowers:requesting-code-review`, `superpowers:verification-before-completion` |
| Ship/open-pr | `superpowers:finishing-a-development-branch` |
