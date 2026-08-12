# Discover / roadmap

Extract candidate epics from the PRD story-map backbone, score and sequence
them, and produce the Now / Next / Later roadmap. This step is a **checkpoint**
and is **skippable for a single-epic product** (see Notes). 

## Inputs

- `docs/flow/product/<slug>/prd.md` (approved) — specifically the story map and
  key requirements.
- `config.yaml → product.prioritization` — determines scoring method. Default
  is RICE; switch to ICE if configured.

## Skippable condition

This stage is optional — skip for a single-epic product (the PRD story map has exactly one user activity) or if the user declines. Document the decision in `docs/flow/product/<slug>/progress.md` with a note: `roadmap skipped — single-epic product` or `roadmap skipped — user declined`. Still tick the stage checkbox.

## Workflow

1. **Extract candidate epics.** Read the PRD story map backbone (top-level user
   activities). Each activity is a candidate epic. Name each epic using the
   activity label from the story map.

2. **Score each epic.** Apply RICE by default (or ICE if `config.yaml`
   specifies `product.prioritization: ice`):

   **RICE:**
   - **Reach** — estimated users reached per week.
   - **Impact** — `0.25 | 0.5 | 1 | 2 | 3` (massive to minimal).
   - **Confidence** — `50% | 80% | 100%` of estimates being accurate.
   - **Effort** — person-weeks to ship.
   - **Score** = `(Reach × Impact × Confidence) / Effort`.

   **ICE** (alternative):
   - **Impact** — `1–10`.
   - **Confidence** — `1–10`.
   - **Ease** — `1–10`.
   - **Score** = `Impact × Confidence × Ease`.

   Every score requires an explicit rationale — do not use placeholder numbers.
   Ground estimates in research findings (user counts, team capacity) where
   possible.

3. **Sequence Now / Next / Later.** Assign each epic to a horizon:

   - **Now** — current quarter; highest-scored epics that are dependencies for
     others or that directly validate the North Star metric.
   - **Next** — next quarter; high-value but not immediately blocking.
   - **Later** — backlog / future; desirable but lower priority.

4. **Fill the roadmap document.** Fill `docs/flow/product/<slug>/roadmap.md` in
   place using `templates/product/roadmap.tmpl.md` as the structure:

   - The RICE/ICE scoring table with all epics and rationales.
   - The Now / Next / Later Mermaid `graph LR` diagram.

5. **Tick the stage.** In `docs/flow/product/<slug>/progress.md`, mark:

   ```
   - [x] roadmap
   ```

## CHECKPOINT

Before presenting for `/flow-approve`, verify:

- Every epic in the scoring table has an explicit numeric rationale (no
  placeholder values).
- The Mermaid roadmap diagram renders without errors.
- At least one epic is in the "Now" horizon.
- The scoring method matches `config.yaml → product.prioritization` (or RICE if
  unset).

**Stop here.** Present the roadmap to the user. Wait for `/flow-approve` to
conclude the Discover phase.

## Notes

- This stage is optional — skip for a single-epic product or if the user declines (tick the checkbox and note the reason). The PRD story map and milestones table already provides sufficient sequencing in that case.
- If two epics have equal scores, prefer the one with higher Confidence — it
  reduces the risk of misjudged assumptions.
- The roadmap is a planning artifact, not a commitment. Horizons will shift as
  research is validated during Build.
