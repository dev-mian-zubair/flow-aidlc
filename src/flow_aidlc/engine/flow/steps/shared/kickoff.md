# kickoff

Load this guide at the start of every Flow task, before any stage begins.

## What to load

1. Read `.flow/config.yaml` — note `guardrails.always_on[]`, `tracker.id_scheme`.
2. Read `.flow/playbook.md` — know the stage sequence and which guides to load per stage.
3. Identify the task id (format: `<TICKET-ID>`), and confirm it exists in the tracker. If no id is known yet — or the id does not exist — do **not** scaffold a worklog; route to `/flow-scope` (the front door that creates the ticket) first. Shape requires a real, tracker-created ticket for traceability.
4. Read `docs/flow/knowledge/practices.md` if present — accumulated working practices from prior tasks; apply them this task.

## Sync + branch (Shape entry only)

> **Scope skips this.** The steps in this section and the next run **only** when
> entering Shape via `/flow-start` (a confirmed ticket, about to do repo work). The
> Scope front door (`/flow-scope`) is **repo-less** — it does not sync, branch, or
> scaffold; it outputs only the ticket. The branch is created at Shape entry (via
> `/flow-start`), off the configured base, before the worklog is scaffolded.

### 1 — Sync

Bring the trunk reference up to date before creating the branch:

```bash
git fetch origin
```

### 2 — Ensure the task branch (off the base)

Work happens on a dedicated branch created off the **base** — default the configured
`vcs.base` (`origin/main`). If you are not already on a task branch for `<TICKET-ID>`, create one:

```bash
git switch -c feat/<area>-<TICKET-ID>-<slug> origin/main    # base = config.yaml → vcs.base (default origin/main)
```

- Name it per the repo convention: `feat/<area>-<TICKET-ID>-<slug>` (or `session/<topic>`).
- If a task branch already exists (e.g. a worktree branched off the base this session
  with no new trunk commits since), that is a no-op — confirm and continue; otherwise
  `git rebase origin/main` to update it.
- **Record the base** on the `Base branch:` line in `docs/flow/worklog/<TICKET-ID>/progress.md` so
  `branch-hardening` and `open-pr` target it. Default is the configured `vcs.base`.

**Epic children default to independent branches off the base** — each child is its own
workstream with its own branch and PR. If this child has a **hard dependency
on a sibling that has not merged yet**, decide the base (recommend A):

- **(A, recommended)** wait for the sibling to merge, then branch off the base — keeps
  the PR simple (targets the trunk) and avoids rebase cascades.
- **(B) stack** — branch off the sibling's branch and set `Base branch:` to it; the PR will
  target that branch. Full stacked-PR support (retarget-on-merge, enforced order) is deferred
  — you manage the rebase/retarget by hand.

Create the branch **before** scaffolding the worklog (next) so every commit — worklog and
code — lands on the feature branch, never on the trunk.

## Create the worklog

Scaffold the worklog directory once, at Shape entry, **on the task branch created above**:

```
cp .flow/templates/progress.tmpl.md   docs/flow/worklog/<TICKET-ID>/progress.md
touch docs/flow/worklog/<TICKET-ID>/journal.md
mkdir -p docs/flow/worklog/<TICKET-ID>/questions
mkdir -p docs/flow/worklog/<TICKET-ID>/shape
mkdir -p docs/flow/worklog/<TICKET-ID>/build
mkdir -p docs/flow/worklog/<TICKET-ID>/ship
```

Do **not** pre-copy requirements, design, or slices templates here — each stage
authors its own artifact from the template when it runs. Do not recreate these
files if the directory already exists — a returning session must use
`steps/shared/resume.md` instead.

## Announce once

Print this note exactly once at the start of a new task session (not on resume):

```
Powered by superpowers — governed path active.
Task: <TICKET-ID>  Stage: <STAGE-NAME>
```

After announcing, load the first stage guide and proceed.
