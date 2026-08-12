# Discover phase — adversarial critique panel review

Invoked by a gated Discover stage agent (`product-prd` / `product-research`) when
panels are enabled, to adversarially stress-test the stage artifact before approval.

## Opt-in / no-op

This step is ONLY active when:
1. `config.product.review` is present in `.flow/config.yaml`, AND
2. the session was started with `/flow-discover --panel` (controlled) or auto mode is running.

When neither condition holds, the stage presents its artifact directly for
`/flow-approve` (controlled) or advances to the next stage (auto) — exactly the
Plan 1 behavior. No panel is dispatched; this file is not read.

## Dispatch

One `product-critic` subagent per lens listed in `config.product.review.lenses`
(default: `market-realist`, `feasibility`, `customer-advocate`, `scope-hawk`).

All `product-critic` subagents are dispatched **in parallel** (conductor → stage
agent (L1) → critics (L2)). Each critic receives:
- The lens it must apply (exactly one lens per critic instance).
- The full stage artifact as read-only input.

This nesting depth (conductor → stage agent → critics) fits within Claude Code's
default nesting limit of 3.

## Consensus

Consensus = **no open high-severity finding** across all critics after a round.

- **High-severity** findings fail the gate and trigger the fix loop.
- **Medium / low** findings are recorded and carried into the artifact's
  `open-questions` section; they are NOT looped on.

## Fix loop

On a failed gate (any high-severity finding remains open):

1. The stage's **own agent** (not the critics) revises the artifact to address
   every open high-severity finding from the current round.
2. The panel re-critiques **the change only** — not the full artifact.
3. Repeat up to `config.product.review.max_rounds` rounds (default 3).

## Outcome

**Convergence (no high-severity findings):**
- Controlled mode → present the improved artifact for `/flow-approve`.
- Auto mode → advance to the next stage automatically.

**Cap without convergence (max_rounds exhausted):**
- Controlled mode → present the artifact WITH residual high-severity findings
  surfaced clearly to the human at the checkpoint for a decision.
- Auto mode → carry the residual findings to the stage report; the conductor
  surfaces them at the end of the Discover phase run.
