# open-pr

Powered by superpowers — invokes `superpowers:finishing-a-development-branch`.

The **terminal stage** of the Flow. It finalizes the branch (including the worklog
audit trail), opens the PR, and stops. The Flow does **not** merge: merge, required
checks + approvals, ticket close, and any migration-lock release are owned by the team
on the host (branch protection on the base branch is authoritative). See
[ADR 0010](../../../knowledge/decisions/0010-ship-ends-at-open-pr.md).

## Goal

Open a clean, review-ready PR whose diff already contains the complete worklog, and
record the PR on the ticket. The Flow's work ends here.

## Inputs

- Branch with all slices verified (all `verify.md` checkboxes checked).
- `branch-hardening` approved and `learnings` complete.

## Ordering principle (why the worklog is committed *before* the PR)

The worklog is a committed part of the branch (ADR 0003), so it must be in the PR's
**initial** diff — which means the wrap-up is committed **before** `OPEN_PR`, not after.
A trailing worklog commit pushed *after* the PR opens re-runs the PR's un-path-filtered
CI workflows on a docs-only change and makes reviewers wait for CI twice. The only fact
that cannot exist before the PR — its number — is recorded on the **ticket** (the host's
native issue↔PR join), not committed back into the branch.

## Steps

### 1 — Finish the branch

Invoke `superpowers:finishing-a-development-branch` to finalize and rebase. **Do not open
the PR or push the final state yet** — the worklog wrap-up (step 5) must be committed first.

### 2 — Pre-PR sanity (so we never open a red PR)

A courtesy pass, not a merge gate — the authoritative gate is the PR's own CI checks +
required approvals. Confirm before opening (use your project's commands from
`config.yaml` → `commands.*`):

- [ ] `commands.test` green.
- [ ] `commands.build` green.
- [ ] `commands.typecheck` green (if configured).
- [ ] Any project-specific migration/schema invariant holds (e.g. a single migration head).
- [ ] `git fetch origin && git rebase <base>` clean — no conflicts (`<base>` = the `Base branch:` in `progress.md`; default the configured `vcs.base`, per [ADR 0011](../../../knowledge/decisions/0011-branch-creation-and-base.md)).
- [ ] All `always_on` guardrails passed in the final `verify.md` (the always_on set from `config.yaml`).

> **Any serialization lock stays held.** If this task holds a project lock (e.g. a
> migration lock in `worklog/MIGRATION-LOCK.md`), do **not** release it here — the lock
> is held until the change lands on the base branch. Releasing it is a post-merge,
> team-owned step (see ADR 0010).

### 3 — Draft the PR

Prepare the PR title (imperative, ≤72 chars) and body (Summary + `Fixes <PI-NNN>` +
Why-body + Test plan). Present this draft at the checkpoint — it is not created yet.

### 4 — CHECKPOINT (approve opening the PR)

Opening a PR is an outward write. **Stop and wait for `/flow-approve`**, presenting both the
PR draft and the worklog wrap-up (step 5) that will be committed. A non-answer is not
approval. `/flow-changes` keeps the workstream here without opening the PR.

### 5 — Finalize the worklog *in the branch* (before the PR exists)

On approval, commit the wrap-up so it is part of the PR's initial diff (one CI run). All of
it is **ticket-keyed** — the PR number does not exist yet and is recorded on the ticket in
step 7:

- Append the final entry to `worklog/<PI-NNN>/journal.md`:
  ```
  <ISO-8601 timestamp>  Ship/open-pr — branch finalized for <PI-NNN>; opening PR. Flow done; team owns merge.
  ```
- Add a **point-in-time** row to `worklog/INDEX.md` (create it with a header row if absent):
  ```
  | <PI-NNN> | <short title> | <date> | pr-open |
  ```
  A fact, not a live status — the Flow ends here and cannot update it, so it never claims
  "merged". Current merge state lives on the host; the PR is reached via the ticket (step 7).
- Mark the `open-pr` checkbox in `worklog/<PI-NNN>/progress.md`.
- Commit: `chore(flow): finalize worklog for <PI-NNN> — opening PR`.

### 6 — Push + open the PR

Push the branch (now carrying the full worklog), then perform `OPEN_PR` via the **tracker
adapter** (`steps/shared/tracker.md`). The PR's **base** is the `Base branch:` recorded in
`progress.md` — normally the configured `vcs.base`; a sibling branch for a stacked epic
child (ADR 0011):

```
OPEN_PR(
  base:  <base>,   # the recorded Base branch — default config.yaml → vcs.base
  title: <imperative subject — ≤72 chars>,
  body:  Summary of changes + Fixes <PI-NNN>,
         Why body (not just what),
         Test plan,
)
```

The body must include `Fixes <PI-NNN>` so the ticket auto-closes **when the team merges**.
Do not merge, squash, or rebase-merge on the team's behalf — the merge method and timing are
theirs.

### 7 — Record the PR on the ticket

Perform `COMMENT` (adapter) on ticket `<PI-NNN>` with the **PR link** (this is where the
issue↔PR number linkage lives — the host maintains it both ways), a one-paragraph summary of
what changed and why, and any follow-on issues filed during the task.

## The team takes it from here (outside the Flow)

- Required CI checks + approvals gate the merge (branch protection on the base branch).
- The team performs the merge (merge queue / captain) — one PR at a time, rebased.
- On merge: `Fixes <PI-NNN>` closes the ticket; any serialization lock is released; the
  branch may be cleaned up. A host-workflow-driven issue lifecycle handles this (separate work).

## Output

- Worklog wrap-up committed **before** the PR, so the PR's initial diff contains the full
  audit trail (single CI run).
- PR opened (review-ready), body carries `Fixes <PI-NNN>`; PR link recorded on the ticket.
- `worklog/INDEX.md` row `pr-open` recorded (ticket-keyed).
- `worklog/<PI-NNN>/journal.md` final entry; `progress.md` `open-pr` checked.
- **Never delete the worklog directory — it is a committed audit trail.**
