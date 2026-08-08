# Auto mode — stage-typed adversarial panel review

Replaces the human `/flow-approve` at a `checkpoint: yes` stage. Dispatch a panel
matched to the stage's artifact, require consensus, fix-loop until clean or park.

The `.flow/STOP` kill-switch is checked between stages (not only between tasks) — a
stage panel that sees `.flow/STOP` halts gracefully after the current stage.

## Consensus
Consensus = every panel member clears with NO open high-severity finding. Any
high-severity finding fails the gate. Findings below high-severity are recorded
and carried to the final report — not looped on.

## Fix loop
On a failed gate: the stage's own agent revises to address the findings, then the
panel re-reviews the change only. Repeat up to `config.execution.review.max_rounds`
(default 5). Converge → advance (no human). Cap without convergence → PARK the task
(`steps/auto/loop.md` step 6).

## Stage-typed panels
| Gate | Artifact | Panel |
|---|---|---|
| Scope/publish, Shape/requirements, Shape/design | prose | `checkpoint-reviewer` + critics (completeness, traceability, ambiguity), `execution.review.panel_size` total |
| Build/code-plan | plan | `checkpoint-reviewer` + a plan critic |
| Build/verify | slice diff | `guardrail-verifier` + a `pr-review-toolkit` subset (`code-reviewer`, `silent-failure-hunter`, `pr-test-analyzer`, `type-design-analyzer`) (+ Impeccable for UI slices) |
| Ship/branch-hardening | branch diff | the full `config.review.branch_hardening` set + `guardrail-verifier` (+ Impeccable for UI slices) |

The code-gate panels ARE `config.review.branch_hardening` (a subset per slice at
Build/verify) — no new review agents.

**UI slices:** for a diff that changes UI, add **Impeccable** to the Build/verify
and branch-hardening panels as the design-quality lens (`/impeccable audit` +
`critique`, checked against `PRODUCT.md`/`DESIGN.md`) — only when the skill is
installed. It complements the pr-review-toolkit code lenses; it does not replace them.
