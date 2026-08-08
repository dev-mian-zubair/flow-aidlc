# verify

Powered by superpowers — invokes `superpowers:requesting-code-review` and
`superpowers:verification-before-completion`.

## Goal

Confirm the slice implementation is correct, reviewed, and guardrail-clean before the checkpoint.

## Inputs

- Workspace changes for this slice (all plan checkboxes checked, tests green).
- `.flow/config.yaml` — `guardrails.always_on[]` and enabled `guardrails.optional[]`.

## Steps

### 1 — Run tests

Run your project's test command (`config.yaml` → `commands.test`; e.g.
`make test`, `npm test`, or `pytest`).

The suite must be green. Stop if it is red — fix and re-run before continuing.

### 2 — Run the guardrail verifier

Load and run every guardrail listed under `guardrails.always_on` in `config.yaml`.
Also run any `guardrails.optional` entries enabled for this task.

The authoritative always-on list is `guardrails.always_on` in `.flow/config.yaml`
— it is the single source of truth and may be empty on a fresh project. Do not
hardcode a guardrail list here.

**A failing guardrail blocks the checkpoint.** Resolve the issue and re-run the
failing guardrail before requesting review.

Record each guardrail result in `worklog/<PI-NNN>/build/<slice-id>/verify.md`, one line per enabled guardrail:

```
- [x] <guardrail-name> — passed
- [x] <guardrail-name> — passed
```

### 3 — Request code review

Invoke `superpowers:requesting-code-review` to open the review request.
Attach the slice diff and the completed `code-plan.md`.

### 4 — Verification before completion

Invoke `superpowers:verification-before-completion` to perform the final
cross-check: confirm the implementation matches the slice design, all edge
cases are covered by tests, and no guardrail is outstanding.

## Checkpoint

Before presenting for `/flow-approve`, dispatch the read-only `checkpoint-reviewer` subagent to verify stage completeness (and traceability at the Shape→Build boundary).

Stop here. Wait for `/flow-approve` before entering `steps/ship/branch-hardening.md` (the first Ship stage).

Approval requires:
- All guardrails passed (recorded in `verify.md`).
- Code review completed and concerns addressed.
- `superpowers:verification-before-completion` sign-off.

## Output

`worklog/<PI-NNN>/build/<slice-id>/verify.md` — all items checked, approved.

## Auto mode

In auto mode (`/flow-auto`) this checkpoint is gated by the stage-typed panel in
`steps/auto/panel-review.md` (guardrail-verifier + the pr-review-toolkit subset on
the slice diff) instead of `/flow-approve`. Same gate, no human stop.
