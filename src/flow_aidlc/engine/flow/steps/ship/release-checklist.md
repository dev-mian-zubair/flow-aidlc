# release-checklist

Powered by superpowers — invokes `superpowers:finishing-a-development-branch`.

## Goal

Gate the branch for merge: all checks pass, PR is open, and the release captain has approved.

## Inputs

- Branch with all slices verified (all `verify.md` checkboxes checked).

## Steps

### 1 — Finishing the branch

Invoke `superpowers:finishing-a-development-branch` to perform the pre-merge checklist.
Follow the skill's output before proceeding to the steps below.

### 2 — Pre-merge checks (merge-queue discipline)

The Flow owns the merge-queue protocol:

- **One PR merged at a time.** Wait for any PR ahead in the queue to land before
  merging this one.
- **Rebase onto the trunk immediately before merging:**
  `git fetch origin && git rebase origin/main`
- **`--no-ff` merge with a why-body** — the merge commit subject is imperative;
  the body explains *why* (not just what); include `Fixes #<PI-NNN>`.
- Delegate the mechanics to `superpowers:finishing-a-development-branch`.
- **If your project uses a coordination lock (e.g. a migration-lock guardrail),
  release it on merge** per your project's convention.

Pre-merge checklist:

- [ ] Project test command green (`config.yaml` → `commands.test`).
- [ ] Project build command green (`config.yaml` → `commands.build`).
- [ ] Project lint command green (`config.yaml` → `commands.lint`).
- [ ] Project typecheck command green, if configured (`config.yaml` → `commands.typecheck`).
- [ ] CI is green.
- [ ] `git fetch origin && git rebase origin/main` clean — no conflicts.
- [ ] All `always_on` guardrails passed in the final `verify.md`.
- [ ] If your project uses a coordination lock, it is released on merge.

### 3 — Open the PR

Perform `OPEN_PR` via the **tracker adapter** (`steps/shared/tracker.md`):

```
OPEN_PR(
  title: <imperative subject — ≤72 chars>,
  body:  Summary of changes + Fixes <PI-NNN>,
         Why body (not just what),
         Test plan,
)
```

The PR body must include `Fixes <PI-NNN>` so the ticket auto-closes on merge.

### 4 — Post a summary to the ticket

Perform `COMMENT` (adapter) on ticket `PI-NNN` with:
- PR link.
- One-paragraph summary of what changed and why.
- Any follow-on issues filed during the task.

### 5 — Follow your project's release/deploy procedure

If this branch is part of a release, follow your project's release/deploy
procedure, if any. Do not improvise a deploy — use the documented,
backup-first sequence your project defines.

## Checkpoint

Stop here. Wait for `/flow-approve` (final approve/merge).

The release captain must:
- Approve the PR on GitHub.
- Perform a `--no-ff` merge to `main` with a why-body.
- Notify the team to `git fetch origin && git rebase origin/main`.
- If your project uses a coordination lock, release it on merge.

## Output

- PR merged to `main`.
- Issue `PI-NNN` closed.
- Team notified.
