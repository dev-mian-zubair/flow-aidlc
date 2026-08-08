# code-plan

Powered by superpowers — uses `superpowers:writing-plans` for structure.

## Goal

Produce a checkboxed, file-by-file implementation plan for the slice. This plan is the sole
artefact that drives `generate.md`; generate nothing without it.

## Inputs

- `worklog/<TICKET-ID>/build/<slice-id>/design.md` — completed slice design.
- `.flow/config.yaml` — active guardrails (note `always_on` list).

## Steps

1. **Invoke `superpowers:writing-plans`** to scaffold the plan structure before writing any
   checkbox items. Follow the output of that skill for sequencing and grouping logic.
2. **Copy the template and fill it:**
   ```bash
   cp .flow/templates/code-plan.tmpl.md worklog/<TICKET-ID>/build/<slice-id>/code-plan.md
   ```
   Fill the SNAPSHOT header (Owner = you, Last updated = today), then under
   `## Steps` add one `- [ ]` checkbox per file to be created or modified
   (migrations first), test files under `## Tests`, set the Scope Guard slice
   boundary, and flag any item touching an always-on guardrail domain with
   `<!-- guardrail: <name> -->`. In particular, flag any checkbox that **adds an
   external dependency** with `<!-- guardrail: dependency-provenance — ADR:
   knowledge/decisions/NNNN -->` so verify can match the install to the approved ADR.
3. **Verify completeness**: every signature and edge case from `design.md` maps to at least one
   checkbox. Apply `steps/shared/overconfidence-prevention.md` — if the design is unclear,
   ask for clarification before planning.
4. **No code yet.** The plan may include short pseudocode snippets inside checkbox descriptions;
   actual implementation belongs in `generate.md`.

## Checkpoint

Stop here. Wait for `/flow-approve` before entering `generate.md`.

The reviewer must confirm:
- All files in scope are accounted for.
- Guardrail-flagged items are acknowledged.
- No scope creep beyond the slice boundary.

## Output

`worklog/<TICKET-ID>/build/<slice-id>/code-plan.md` — approved, all checkboxes unchecked.
