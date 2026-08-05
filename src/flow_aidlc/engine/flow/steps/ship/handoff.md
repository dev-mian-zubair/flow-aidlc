# handoff

## Goal

Close out the task cleanly so the next session (or team member) finds a tidy state.

## When to run

After the PR is merged and the issue is closed (checkpoint in `release-checklist.md` approved).

## Steps

### 1 — Update the worklog INDEX

Open `worklog/INDEX.md` and add an entry for this task:

```
| PI-NNN | <short title> | <date merged> | main@<merge sha> | closed |
```

If `worklog/INDEX.md` does not exist, create it with that header row first.

### 2 — Release the coordination lock (if your project uses one)

If your project uses a coordination lock (e.g. a serialized-write guardrail) and
this task held it, confirm it is reset to its unheld state. If it was not released
at merge time, reset it now per your project's convention:

```
**Held by:** _nobody_
**Task:** —
**Since:** —
```

Commit the reset with message: `chore(flow): release coordination lock — <PI-NNN> merged`.

### 3 — Close the ticket

Confirm ticket `PI-NNN` is closed. If auto-close via `Fixes <PI-NNN>` did not trigger,
perform `CLOSE` (adapter) and a `COMMENT` referencing the merge commit.

### 4 — Update the journal

Append a final entry to `worklog/<PI-NNN>/journal.md`:

```
<ISO-8601 timestamp>  Ship/handoff complete — PR merged, issue closed, INDEX updated.
```

### 5 — Update the progress file

In `worklog/<PI-NNN>/progress.md`, mark the Ship/handoff stage checkbox as done.

### 6 — Clean up (optional)

If the feature branch is no longer needed locally, it may be deleted after the merge sha is
confirmed in `main`. Never delete the worklog directory — it is a committed audit trail.

## Output

- `worklog/INDEX.md` updated.
- Coordination lock reset to its unheld state (if your project uses one).
- Issue `PI-NNN` closed on GitHub.
- `worklog/<PI-NNN>/journal.md` final entry written.
- `worklog/<PI-NNN>/progress.md` fully checked.
