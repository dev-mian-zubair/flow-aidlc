# Discover / vision

Articulate the strategic case for the product — who it is for, what problem it
solves, and how success will be measured. This step is a **checkpoint**.

## Powered by superpowers

Invoke `superpowers:brainstorming` to explore the idea before committing to
writing.

```
/superpowers:brainstorming
```

Use the brainstorming output to surface:

- The specific, evidenced pain point (who has it, how often, at what cost).
- The primary persona(s) — role, context, and what they care about most.
- The North Star metric — the single number that best signals the problem is
  solved, with a target value and time horizon.
- The Outcome / OKR — objective + 2–3 measurable, time-bound key results.
- Non-goals — what this product explicitly does **not** do.

## Inputs

- The raw idea or one-liner from `Discover / intake`.
- The scaffolded product folder at `docs/flow/product/<slug>/`.

## Workflow

1. **Brainstorm.** Run `superpowers:brainstorming`. Do not write anything until
   the session surfaces clear answers to all five vision sections.

2. **Draft the vision document.** Fill `docs/flow/product/<slug>/vision.md` in
   place (the stub was created by intake). Produce all five sections from
   `.flow/templates/product/vision.tmpl.md`:

   - Problem
   - Target users
   - North Star metric
   - Outcome / OKR
   - Non-goals

   Keep every section — mark `<!-- N/A -->` rather than deleting one that does
   not apply.

3. **Tick the stage.** In `docs/flow/product/<slug>/progress.md`, mark:

   ```
   - [x] vision
   ```

## CHECKPOINT

Before presenting for `/flow-approve`, verify:

- All five template sections are filled (no placeholder text remaining).
- The North Star metric has a concrete target value and time horizon.
- At least one non-goal is stated.

**Stop here.** Present the vision document to the user. Wait for `/flow-approve`
before advancing to `Discover / pr-faq`.

## Notes

- The North Star metric stated here is the anchor for PRD success metrics — do
  not change it silently in later stages. If research invalidates it, surface
  that explicitly at the PRD checkpoint.
- Keep the vision document strategy-level; tactical decisions belong in the PRD
  and roadmap.
