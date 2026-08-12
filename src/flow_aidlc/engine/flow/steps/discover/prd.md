# Discover / prd

Consolidate the vision, PR-FAQ, and research findings into a single authoritative
Product Requirements Document. Every claim in the PRD must be grounded in an
upstream artifact — no new uncited market assertions. This step is a
**checkpoint**.

## Inputs

- `docs/flow/product/<slug>/vision.md` (approved).
- `docs/flow/product/<slug>/pr-faq.md` (approved).
- `docs/flow/product/<slug>/research.md` (approved).

## Workflow

1. **Synthesise upstream artifacts.** Read all three approved artifacts. For
   each section of the PRD, identify the source artifact that grounds the
   content. Do not introduce new market claims that do not appear in research.md.

2. **Draft the PRD.** Fill `docs/flow/product/<slug>/prd.md` in place using
   `templates/product/prd.tmpl.md` as the structure:

   - **Problem** — restate the validated problem from Vision in one crisp
     paragraph, tying in research evidence.
   - **Users / personas** — from Vision, confirmed by research.
   - **Success metrics** — every metric ties directly to the North Star metric
     defined in Vision. Fill the metrics table with baseline, target, and time
     horizon. State the source artifact next to any metric derived from research
     data.
   - **Story map** — extract user activities from the PR-FAQ press release and
     FAQ; decompose into tasks and stories. Render as a Mermaid `graph TD`
     diagram. The backbone (top row of activities) becomes the input to the
     roadmap stage.
   - **Scope** — what is explicitly in scope for the first release.
   - **Non-goals** — from Vision; add any new non-goals surfaced by research.
   - **Key requirements** — each requirement is testable and uses RFC 2119
     language (MUST / SHOULD / MAY). Ground each requirement in an upstream
     artifact (e.g., `[vision] North Star metric requires…` or
     `[research] governance screen requires…`).
   - **Milestones** — high-level target dates derived from the North Star time
     horizon.

3. **Cite upstream artifacts.** For any non-obvious claim, add an inline
   citation: `[vision]`, `[pr-faq]`, or `[research]`. Ground market-size
   numbers and technical constraints in `research.md` sources.

4. **Tick the stage.** In `docs/flow/product/<slug>/progress.md`, mark:

   ```
   - [x] prd
   ```

## CHECKPOINT

Before presenting for `/flow-approve`, verify:

- The North Star metric in the success metrics table matches the metric in
  Vision exactly (same number and time horizon).
- The Mermaid story map renders without errors and has at least one activity
  column.
- Every key requirement is traceable to an upstream artifact.
- No new market claims appear that are not grounded in research.md.

**Stop here.** Present the PRD to the user. Wait for `/flow-approve` before
advancing to `Discover / roadmap`.

## Notes

- The story map backbone (user activities) is the direct input to the roadmap
  stage — make it concrete and complete.
- Requirements must be traceable — Build slices will reference PRD requirement
  IDs. Use a consistent numbering scheme (REQ-01, REQ-02, …).
- If research surfaced a showstopper (e.g., no tech option passes governance),
  the PRD should document the constraint and flag it rather than glossing over
  it.
