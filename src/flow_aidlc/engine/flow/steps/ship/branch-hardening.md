# Ship / branch-hardening

Harden the **assembled branch** before it becomes a PR. Build/verify reviewed each
slice in isolation; this reviews the whole stack — cross-slice integration, whole-diff
patterns, and coverage gaps that only appear once every slice is stacked. This step
runs **first in Ship**, before `release-checklist`, and is a **checkpoint**.

## Goal

Run the configured `pr-review-toolkit` review agents across the full branch diff,
resolve high-severity findings, and gate the branch before the PR is opened.

## Inputs

- The branch, all slices verified (every `verify.md` checked).
- `config.yaml → review.branch_hardening` — the agent set to run.

## Steps

### 1 — Compute the branch diff

```bash
git fetch origin && git diff origin/main...HEAD --stat
```

The review target is the full set of changes on this branch vs `origin/main`.

### 2 — Dispatch the review agents (in parallel) on the diff

Dispatch each agent listed in `config.yaml → review.branch_hardening` on the branch
diff. Default set:

- `pr-review-toolkit:code-reviewer` — bugs, guideline / style adherence
- `pr-review-toolkit:silent-failure-hunter` — swallowed errors, bad fallbacks
- `pr-review-toolkit:pr-test-analyzer` — test-coverage completeness
- `pr-review-toolkit:type-design-analyzer` — type / encapsulation quality
- `pr-review-toolkit:comment-analyzer` — comment accuracy vs code

`pr-review-toolkit:code-simplifier` is intentionally **excluded** here — it mutates
code; simplification belongs in Build, not a pre-merge gate. These agents **report**
findings; fixes are applied separately (step 4).

### 3 — Collect + record findings

Dedupe findings across agents and record them to
`worklog/<ID>-NNN/ship/branch-hardening.md`, each with: agent, `file:line`, severity
(`high` | `medium` | `low`), and a one-line description.

### 4 — Resolve high-severity findings

**A high-severity finding blocks the checkpoint.** Fix it in the workspace (a targeted
change — not a new slice unless the fix is large enough to warrant one), re-run the
affected agent, and confirm it clears. Medium / low findings are recorded; address
them or **explicitly defer** with a one-line reason.

### 5 — CHECKPOINT

Before presenting for `/flow-approve`, dispatch the read-only `checkpoint-reviewer`
subagent to confirm every high-severity finding is resolved and the record is complete.

**Stop here.** Present the findings summary (resolved + deferred) to the user. Wait
for `/flow-approve` before advancing to `release-checklist`.

## Output

`worklog/<ID>-NNN/ship/branch-hardening.md` — findings, resolutions, and any explicit
deferrals; all high-severity resolved.

## Notes

- Complements Build/verify (per-slice) — catches whole-branch and cross-slice issues
  that per-slice review cannot see.
- Runs on the **local branch diff** — no tracker/PR required, so it gates *before* the
  PR is opened in `release-checklist`.
- If hardening surfaces a design-level problem, don't paper over it — raise it and
  consider whether a slice needs rework before merge.
