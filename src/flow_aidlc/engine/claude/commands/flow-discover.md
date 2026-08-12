---
description: Begin a greenfield product-definition workstream — scaffold product artifacts, then run the Discover phase.
argument-hint: "\"<new product idea>\" [--panel]"
---

**`/flow-discover` is a distinct entry point — it is NOT part of the `/flow-start` (Shape) path.** It turns a new-product idea into grounded, gated product-definition artifacts under `docs/flow/product/<slug>/`. This iteration supports **greenfield only** and does not hand off to Scope / Build / Ship.

**Step 1 — Read the playbook.** Load `.flow/playbook.md` to orient to stage rules, checkpoint protocol, and loading conventions before dispatching any stage guide.

**Step 2 — Dispatch `product-intake`.** Load `.flow/steps/discover/intake.md`. `product-intake` classifies the idea as **greenfield** or **brownfield** and, for greenfield, scaffolds `docs/flow/product/<slug>/`.

- If `product-intake` reports **brownfield**, **stop immediately** and tell the user: *"This idea looks like brownfield work (it targets an existing product). `/flow-discover` is greenfield-only this iteration — use `/flow-start` with the relevant tracker ticket instead."* Do not advance to any further stage.

**Adversarial critique panels (opt-in).** Pass `--panel` to have the gated stages `product-research` and `product-prd` dispatch a parallel adversarial critique panel (`steps/discover/panel-review.md`, one `product-critic` per lens in `config.product.review.lenses`) that stress-tests the artifact and drives a fix-loop BEFORE the `/flow-approve` checkpoint. Panels are enabled when `config.product.review` is present AND the run was started with `/flow-discover --panel`. Without `--panel`, Discover runs the default sequential path (no panels). Auto-mode Discover is not wired this iteration; Discover panels are controlled-mode-only, enabled via `/flow-discover --panel`.

**Step 3 — Run the Discover phase stages in order.** For a confirmed greenfield classification, load and execute each stage guide in sequence, pausing at every `checkpoint: yes` stage for `/flow-approve` before advancing:

1. **vision** — load `.flow/steps/discover/vision.md`; invoke `superpowers:brainstorming`; **checkpoint** → present the artifact to the human; wait for `/flow-approve`.
2. **pr-faq** — load `.flow/steps/discover/pr-faq.md`; **checkpoint** → present the artifact to the human; wait for `/flow-approve`.
3. **research** — load `.flow/steps/discover/research.md`; invoke `deep-research`; **checkpoint** → present the artifact to the human; wait for `/flow-approve`.
4. **prd** — load `.flow/steps/discover/prd.md`; **checkpoint** → present the artifact to the human; wait for `/flow-approve`.
5. **roadmap** (`product-roadmap`) — load `.flow/steps/discover/roadmap.md` (**optional** — skip for a single-epic product or if the user declines); **checkpoint** → present the roadmap to the human; wait for `/flow-approve`.

All product-definition artifacts are written under `docs/flow/product/<slug>/`. At each checkpoint, the human reviews the stage artifact and runs `/flow-approve` to advance; `flow check` (product-consistency) validates artifact completeness. The worklog-scoped `checkpoint-reviewer` subagent does NOT run in Discover — it operates on `docs/flow/worklog/<TICKET-ID>/` paths and does not apply to product units.

**This path terminates after `roadmap`.** It does not chain into `/flow-start`, Scope, Build, or Ship. If the user wants to progress from product definition to ticket-tracked delivery, they should open a Scope workstream manually using the outputs from this phase as source material.
