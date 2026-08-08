# Ship / branch-hardening

Harden the **assembled branch** before it becomes a PR. Build/verify reviewed each
slice in isolation; this reviews the whole stack — cross-slice integration, whole-diff
patterns, and coverage gaps that only appear once every slice is stacked. This step
runs **first in Ship**, before `learnings` and `open-pr`, and is a **checkpoint**.

## Goal

Run the configured `pr-review-toolkit` review agents across the full branch diff,
resolve high-severity findings, and gate the branch before the PR is opened.

## Inputs

- The branch, all slices verified (every `verify.md` checked).
- `config.yaml → review.branch_hardening` — the agent set to run.

## Steps

### 1 — Compute the branch diff

The review target is this branch vs its **base** — the `Base branch:` recorded in
`worklog/<TICKET-ID>/progress.md` (default the configured `vcs.base`; a sibling branch for a
stacked epic child, since epic children are independent branches):

```bash
git fetch origin && git diff <base>...HEAD --stat        # <base> = the recorded Base branch
```

### 1b — Compute the blast radius (IMPACT_OF_DIFF)

Per-file review sees the diff; it does **not** see who *outside* the diff depends on
what the diff changed. Compute the **out-of-diff dependents** of the changed symbols —
the callers a changed contract could break that no reviewer would otherwise open — with
`IMPACT_OF_DIFF` (`steps/shared/graph.md`). This is a **local, pre-PR** diff, so use
`graphify affected "<sym>"` per changed symbol (CLI), or `get_neighbors` over the graph
MCP reading the incoming `<--` edges. (Do **not** use the MCP `get_pr_impact` here — it
needs an existing GitHub PR number; branch-hardening runs before the PR exists.)

Record the impact set (out-of-diff symbols + `file:line`) and **pass it to the review
agents in step 2** as focus context: *"these symbols outside the diff depend on changed
contracts — confirm the change doesn't break them."* This turns whole-branch review
into blast-radius-aware review.

If the graph is unavailable or stale (rebuild with the configured `graph.build`), note
it and proceed with the diff-only review — this enrichment is additive, never a blocker.

### 2 — Dispatch the review agents (in parallel) on the diff

Dispatch each agent listed in `config.yaml → review.branch_hardening` on the branch
diff, **plus the blast-radius context from step 1b**. Default set:

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
`worklog/<TICKET-ID>/ship/branch-hardening.md`, each with: agent, `file:line`, severity
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
for `/flow-approve` before advancing to `learnings`.

## Output

`worklog/<TICKET-ID>/ship/branch-hardening.md` — findings, resolutions, and any explicit
deferrals; all high-severity resolved.

## Notes

- Complements Build/verify (per-slice) — catches whole-branch and cross-slice issues
  that per-slice review cannot see.
- Runs on the **local branch diff** — no tracker/PR required, so it gates *before* the
  PR is opened in `open-pr`. It is a **pre-PR self-review**: it front-loads cleanup so the
  branch is clean before humans review it on the actual PR (human review + the PR's
  required CI checks are the team's gate — the Ship phase ends at opening the PR).
- If hardening surfaces a design-level problem, don't paper over it — raise it and
  consider whether a slice needs rework before merge.
- **Optional security pass:** for changes touching auth, input handling, secrets, or
  external surfaces, add a dedicated security review here (the first-party
  `security-guidance` plugin or the `/security-review` command) alongside the configured
  `pr-review-toolkit` agents. For a runnable UI/endpoint, optionally smoke the app via
  the Playwright MCP — see `INTEGRATIONS.md → Optional integrations`.

## Auto mode

In auto mode this checkpoint is gated by the full `config.review.branch_hardening`
panel + guardrail-verifier via `steps/auto/panel-review.md` (no `/flow-approve`);
on consensus the run proceeds to `steps/auto/merge.md`.
