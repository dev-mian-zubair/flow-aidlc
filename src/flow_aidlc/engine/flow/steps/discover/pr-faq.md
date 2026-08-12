# Discover / pr-faq

Write the Amazon Working-Backwards document — a future-dated press release and
FAQ — to pressure-test the product idea before any engineering begins. The
`## Riskiest assumptions` section is the explicit hand-off that focuses the
research stage. This step is a **checkpoint**.

## When to run

Always. Every greenfield product needs a PR-FAQ before research and PRD.

## Inputs

- `docs/flow/product/<slug>/vision.md` (approved).
- Any user-supplied context about the target market, pricing intent, or
  competitive landscape.

## Workflow

1. **Read the vision document.** Extract the problem, target users, North Star
   metric, and non-goals.

2. **Draft the PR-FAQ.** Fill `docs/flow/product/<slug>/pr-faq.md` in place
   using `templates/product/pr-faq.tmpl.md` as the structure:

   - **Press release** — headline, dateline, problem paragraph, solution
     paragraph, customer quote, call to action.
   - **FAQ — internal** — Why now? Why us? Riskiest assumptions. What could go
     wrong?
   - **FAQ — customer** — What does it do? What does it cost? When is it
     available?
   - **`## Riskiest assumptions`** (standalone section) — list every assumption
     the thesis rests on as falsifiable statements. This section is the direct
     input to the research stage; be explicit and complete.

3. **Surface the riskiest assumptions.** The `## Riskiest assumptions` list must
   contain at least two entries. Each entry is a falsifiable statement of the
   form: *"[User segment] will [do X] because [Y]"* or *"The market is large
   enough that [measurable outcome]."* Vague beliefs are not sufficient — make
   them testable.

4. **Tick the stage.** In `docs/flow/product/<slug>/progress.md`, mark:

   ```
   - [x] pr-faq
   ```

## CHECKPOINT

Before presenting for `/flow-approve`, verify:

- All three FAQ sections are complete (no placeholder text remaining).
- The `## Riskiest assumptions` section contains at least two falsifiable
  statements.
- The press release reads as if the product already shipped and is genuinely
  compelling.

**Stop here.** Present the PR-FAQ to the user. Wait for `/flow-approve` before
advancing to `Discover / research`.

## Notes

- Write the press release in the past tense ("today, Acme launched…"), not
  future tense. The discipline of writing as if it shipped forces concreteness.
- The riskiest assumptions list is the primary deliverable from this stage — the
  research agent uses it verbatim as its research questions. Make it specific.
- Do not resolve the riskiest assumptions here; that is what research is for.
