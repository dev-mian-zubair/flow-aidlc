# Shape / requirements

Produce the requirements document and resolve any remaining open questions before
design begins. This step is a **checkpoint**.

## Powered by superpowers

Invoke `superpowers:brainstorming` to explore requirements before committing them
to writing.

```
/superpowers:brainstorming
```

Use the brainstorming output to surface:

- Functional requirements derived from the ticket's acceptance criteria.
- Non-functional requirements (performance, security, observability, accessibility).
- Constraints inherited from the existing-code map (if Shape / map-existing ran).
- Constraints and the chosen dependency from the external research (if Shape / research ran).
- Edge cases and failure modes that acceptance criteria do not yet cover.

## Guardrail opt-in prompts

After brainstorming, present these prompts for the user to opt in or out:

```
Optional guardrails for this task:
[ ] security-baseline    — OWASP top-10 checks at Build/verify
[ ] resiliency-baseline  — retry, timeout, and circuit-breaker checks
[ ] test-coverage        — coverage threshold enforced at Build/verify

Enable any? (list names, or "none")
```

Record enabled optional guardrails in `docs/flow/worklog/<TICKET-ID>/progress.md` under a
`## Guardrails` section. The always-on guardrails (`migration-safety`,
`budget-integrity`, `authz-completeness`, `router-safety`, `license-sku-gating`) are already active.

## Produce a question file

For any requirement that is still ambiguous, write one entry in
`docs/flow/worklog/<TICKET-ID>/questions/requirements.questions.md` per
`steps/shared/question-format.md`.

Apply `steps/shared/overconfidence-prevention.md` when deciding whether to ask
vs infer — never proceed past unresolved ambiguity.

Resolve all blocking questions before writing the requirements document.

## Complete the guardrail impact checklist

Before drafting the requirements document, fill the `## Guardrail impact
checklist` per `steps/shared/gotcha-checklist.md`. For each always-on invariant,
state the impact or `none`. A non-`none` impact means that guardrail will be
enforced at Build/verify — plan for it now, not later.

## Write the requirements document

Copy the template as the skeleton, then fill it in place:

```bash
cp .flow/templates/requirements.tmpl.md docs/flow/worklog/<TICKET-ID>/shape/requirements.md
```

Fill the SNAPSHOT header (Owner = you, Last updated = today), every `[Answer]:`,
the FR-N/NFR-N rows, and the guardrail-impact checklist (per
`steps/shared/gotcha-checklist.md`). Per `steps/shared/content-validation.md`,
keep every template section — mark one `<!-- N/A -->` rather than deleting a section
that does not apply.

## CHECKPOINT

This is a checkpoint stage: the conductor dispatches the read-only `checkpoint-reviewer` to verify stage completeness (and traceability at the Shape→Build boundary) before `/flow-approve`. This agent does not dispatch it — it presents its artifact and returns.

**Stop here.** Present the requirements document and any open questions to the
user. Wait for `/flow-approve` before advancing to Shape / design.

## Notes

- Requirements must be traceable — each Build slice will reference requirement ids.
- Do not include design decisions here; those belong in Shape / design.
