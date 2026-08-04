# resume

Use this guide to rebuild working state after a context reset (new session, new
agent window, or mid-task handoff).

## Step 1 — identify the task

The task id (`PI-NNN`) must be provided by the caller. If it is not, ask before
doing anything else.

## Step 2 — read progress

```
worklog/<PI-NNN>/progress.md
```

Find the first unchecked stage checkbox (`- [ ]`). That is the current stage.
All stages above it are complete; do not re-run them.

## Step 3 — load the current stage guide

Look up the current stage in `.flow/playbook.md` to find its `load:` path.
Read that guide fully.

## Step 4 — load dependency artifacts

Read the output files that the current stage consumes. At minimum:

- `worklog/<PI-NNN>/shape/requirements.md` — always relevant from Shape onward.
- `worklog/<PI-NNN>/shape/slices.md` — always relevant from Build onward.
- The output file of the immediately preceding stage (e.g., if resuming
  Build/generate, read `worklog/<PI-NNN>/build/<slice>/code-plan.md`).

Do not load files that the current stage does not consume.

## Step 5 — read the journal tail

```
worklog/<PI-NNN>/journal.md   (last few ## <datetime> entries)
```

This surfaces any decisions, blockers, or context notes recorded in the
previous session.

## Step 6 — announce and continue

Print:

```
Resumed: <PI-NNN>  Current stage: <stage name>
```

Then continue from the current stage as if it is just starting.
