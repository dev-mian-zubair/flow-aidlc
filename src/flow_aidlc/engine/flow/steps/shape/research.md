# Shape / research

Evaluate the external landscape — third-party services, libraries, or tools —
before design commits to one. This step is **CONDITIONAL** (run only when the
feature needs an external dependency the current stack does not provide) and is a
**checkpoint** (adopting a third-party is a consequential, hard-to-reverse choice).

## When to run

Run when a required capability is **not present in the current stack /
Knowledge Map** — e.g. "send SMS", "translate strings", "process payments",
"OCR a PDF". `shape-intake` (or `shape-requirements`) routes here on that signal.
Skip entirely when the work uses only what the project already has.

## Powered by superpowers

Invoke the `deep-research` skill to run the research: fan-out web search, fetch
official docs/sources, adversarially verify claims, and synthesise a **cited**
findings set. Use `WebFetch` for exact API/library docs.

Frame a specific question first (capability + hard constraints); if the request
is under-specified, ask 1–2 clarifying questions before researching. Apply
`steps/shared/overconfidence-prevention.md`.

## Evaluate against the project's posture

For every candidate, run the **governance screen** — self-host / air-gap, data
egress / residency, license compatibility (any license boundary your CI gates),
security-scan expectations (dependency-audit / SAST / container-scan), and
maintenance risk. A failing check is a blocker to surface **here** — far cheaper
than discovering it at Build/CI.

## Write the research document

Copy the template as the skeleton, then fill it in place:

```bash
cp .flow/templates/research.tmpl.md docs/flow/worklog/<TICKET-ID>/shape/research.md
```

Fill the SNAPSHOT header, the Question, Options (with sources), Recommendation,
Trade-offs, Governance screen, Integration notes, and Open questions. Cite a
source (URL) for every non-obvious external claim — do not assert from memory.
Per `steps/shared/content-validation.md`, keep every section — mark one
`<!-- N/A -->` rather than deleting one that does not apply.

## CHECKPOINT

This is a checkpoint stage: the conductor dispatches the read-only `checkpoint-reviewer`
to verify completeness (every option cited, the governance screen complete, a clear
recommendation) before `/flow-approve`. This agent does not dispatch it — it presents
its artifact and returns.

**Stop here.** Present the recommendation + governance screen to the user. Wait
for `/flow-approve` before advancing to Shape / requirements. Adopting the chosen
dependency is a cross-cutting decision — it graduates to `docs/flow/knowledge/decisions/` at
Shape / design, referencing this document.

## Notes

- Research findings feed `requirements` (constraints / NFRs from the chosen tool)
  and `design` (the adoption ADR + integration seams).
- If **no** option clears the governance screen, say so and return to
  `scope-story` to reconsider the ticket's scope rather than forcing a bad
  dependency.
- **Name the exact package(s)** (and version / registry where it matters) the
  recommendation adopts. The `dependency-provenance` guardrail (if enabled)
  matches installed dependencies against the approved ADR at verify, so a vague
  "some i18n library" — or a substituted one — will block the Build checkpoint.
