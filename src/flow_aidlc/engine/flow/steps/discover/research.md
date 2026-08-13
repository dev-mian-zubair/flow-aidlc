# Discover / research

Validate the riskiest assumptions from the PR-FAQ, evaluate the market and
competitive landscape, and recommend a tech stack that passes the governance
screen. This step is **conditional-depth** (for a whole product, it always
runs — tech-stack choice is a consequential, hard-to-reverse decision) and is a
**checkpoint**.

## When to run

Always for a greenfield product. Skip only if the product's entire tech stack is
already fixed by an existing platform decision (rare; document the reason if
skipping).

## Powered by superpowers

Invoke the `deep-research` skill to run the research: fan-out web searches,
fetch official docs/sources, adversarially verify claims, and synthesise a
**cited** findings set.

```
/deep-research
```

Frame specific questions first — derived directly from the `## Riskiest
assumptions` in `docs/flow/product/<slug>/pr-faq.md`. Do not research in the
abstract; each question maps to one riskiest assumption. Apply
`steps/shared/overconfidence-prevention.md`.

## Inputs

- `docs/flow/product/<slug>/pr-faq.md` (approved), specifically the
  `## Riskiest assumptions` section.
- `docs/flow/product/<slug>/vision.md` (approved) for target-user and market
  context.

## Workflow

1. **Extract research questions.** For each riskiest assumption in the PR-FAQ,
   reframe it as a research question. Example: assumption "developers will pay
   $20/month for automated code review" → question "What is the current
   willingness to pay for developer tooling subscriptions, and what price points
   do comparable tools charge?"

2. **Run deep-research.** Invoke `deep-research` with the full list of
   questions. Cite every non-obvious external claim — do not assert from memory.

3. **Evaluate the tech stack.** For each candidate stack component, run the
   governance screen:

   - **License** — name the license and state compatibility with the project's
     license posture.
   - **Hosting** — self-hosted / SaaS / hybrid; confirm data-residency
     requirements are met.
   - **Maturity** — GA / beta / alpha; community size; date of last stable
     release.
   - **Cost** — pricing model and estimated cost at the target scale (from the
     North Star metric).

   A failing governance screen item is a blocker. Surface it here — far cheaper
   than discovering it during Build.

4. **Fill the research document.** Fill `docs/flow/product/<slug>/research.md`
   in place using `.flow/templates/product/research.tmpl.md` as the structure. Produce
   all sections: Research questions, Market & demand, Competitors, Recommended
   tech stack (with governance screen), Trade-offs, Open questions, Sources.

5. **Graduate the tech-stack decision.** Write a decision record in
   `docs/flow/knowledge/decisions/` per `steps/shared/decision-format.md`.
   Reference the decision number in `research.md`.

6. **Tick the stage.** In `docs/flow/product/<slug>/progress.md`, mark:

   ```
   - [x] research
   ```

## Critique panel (opt-in)

This section is active **only when panels are enabled** (`config.product.review` present AND the session was started with `/flow-discover --panel`). When disabled, skip directly to CHECKPOINT — this is the default Plan 1 behavior.

When panels are enabled:

1. Invoke `.flow/steps/discover/panel-review.md` on the drafted research document.
2. Dispatch one `product-critic` subagent per lens in `config.product.review.lenses` — all in parallel — critiquing the recommendation, tech-stack choice, and governance screen.
3. **Consensus** = no open high-severity finding across all critics after a round.
4. **Fix loop** — on any high-severity finding: the `product-research` agent (not the critics) revises the research document to address each open high-severity finding, then the panel re-critiques the change only. Repeat up to `config.product.review.max_rounds` rounds (default 3).
5. Proceed to CHECKPOINT with the improved research document. If max_rounds is exhausted without convergence, surface residual high-severity findings clearly to the human at the checkpoint for a decision.

Medium and low findings are recorded in the research document's open-questions section and are NOT looped on.

## CHECKPOINT

Before presenting for `/flow-approve`, verify:

- Every research question maps to a riskiest assumption from the PR-FAQ.
- Every non-obvious external claim has a cited source URL.
- The governance screen is complete for the recommended stack (all four checks
  filled, not `<!-- N/A -->`).
- A decision record has been written and is referenced in `research.md`.

**Stop here.** Present the research findings and tech-stack recommendation to
the user. Wait for `/flow-approve` before advancing to `Discover / prd`.

## Notes

- If no tech-stack option clears the governance screen, say so explicitly and
  propose narrowing the scope rather than adopting a failing dependency.
- Name the exact packages and version ranges the recommendation adopts — a vague
  "some ML framework" will cause problems at Build.
- Research findings directly ground the PRD: market evidence supports the
  problem statement; governance results constrain the key requirements.
