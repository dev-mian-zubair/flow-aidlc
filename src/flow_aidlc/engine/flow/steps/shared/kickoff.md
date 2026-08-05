# kickoff

Load this guide at the start of every Flow task, before any stage begins.

## What to load

1. Read `.flow/config.yaml` — note `guardrails.always_on[]`, `tracker.id_scheme`.
2. Read `.flow/playbook.md` — know the stage sequence and which guides to load per stage.
3. Identify the task id (format: `PI-NNN`), and confirm it exists in the tracker. If no id is known yet — or the id does not exist — do **not** scaffold a worklog; route to `/flow-scope` (the front door that creates the ticket) first. Shape requires a real, tracker-created ticket for traceability.
4. Read `knowledge/practices.md` if present — accumulated working practices from prior tasks; apply them this task.

## Sync first

Before doing anything else, bring the local branch up to date with the trunk:

```bash
git fetch origin && git rebase origin/main
```

If the worktree was branched directly off `origin/main` in this session and no
new commits have landed since, this is a no-op — confirm and continue.

## Create the worklog

Scaffold the worklog directory once, at task start:

```
cp .flow/templates/progress.tmpl.md   worklog/<PI-NNN>/progress.md
touch worklog/<PI-NNN>/journal.md
mkdir -p worklog/<PI-NNN>/questions
mkdir -p worklog/<PI-NNN>/shape
mkdir -p worklog/<PI-NNN>/build
mkdir -p worklog/<PI-NNN>/ship
```

Do **not** pre-copy requirements, design, or slices templates here — each stage
authors its own artifact from the template when it runs. Do not recreate these
files if the directory already exists — a returning session must use
`steps/shared/resume.md` instead.

## Announce once

Print this note exactly once at the start of a new task session (not on resume):

```
Powered by superpowers — governed path active.
Task: <PI-NNN>  Stage: Scope/clarify
```

After announcing, load the first stage guide and proceed.
