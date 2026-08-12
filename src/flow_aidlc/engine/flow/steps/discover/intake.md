# Discover / intake

Classify the repo, derive a slug, scaffold the product folder, and route to the
first substantive stage. This step has **no checkpoint** — it is a fast routing
step, not an artifact step.

## Detect greenfield vs brownfield

Inspect the repository before writing anything:

1. Check whether a code graph exists (`docs/flow/knowledge/code-graph/` or any
   equivalent committed graph artifact).
2. Check whether there is substantial committed source code (more than a handful
   of scaffolding files).

**If brownfield:** report

> "brownfield/revamp not supported this iteration — greenfield only"

and **STOP**. Do not proceed.

**If greenfield:** continue.

## Inputs

- The raw idea or one-liner the user supplied.
- The repository state (committed files only — ignore uncommitted work).

## Workflow

1. **Derive the slug.** Convert the idea to a kebab-case identifier (lowercase
   words, hyphens, no punctuation). Example: "AI meeting summariser" →
   `ai-meeting-summariser`. Confirm the slug with the user if it is ambiguous.

2. **Scaffold the product folder.**

   ```bash
   mkdir -p docs/flow/product/<slug>
   ```

   Copy and fill `templates/product/progress.tmpl.md` → `docs/flow/product/<slug>/progress.md`.
   Fill the frontmatter fields:

   - `id: <slug>`
   - `kind: product`
   - `grounding: greenfield`
   - `status: in-discovery`

   Leave all stage checkboxes unchecked (`- [ ]`).

3. **Create artifact stubs.** Copy each template stub (do not fill content yet —
   they will be filled by their respective stage agents):

   ```
   templates/product/vision.tmpl.md   → docs/flow/product/<slug>/vision.md
   templates/product/pr-faq.tmpl.md   → docs/flow/product/<slug>/pr-faq.md
   templates/product/research.tmpl.md → docs/flow/product/<slug>/research.md
   templates/product/prd.tmpl.md      → docs/flow/product/<slug>/prd.md
   templates/product/roadmap.tmpl.md  → docs/flow/product/<slug>/roadmap.md
   ```

4. **Route to vision.** Announce the slug, confirm the folder is scaffolded,
   and advance to `Discover / vision`.

## Notes

- Never write a slug that collides with an existing folder under
  `docs/flow/product/`. If a collision exists, ask the user to disambiguate.
- Do not begin any discovery work here; intake is classification and routing
  only.
