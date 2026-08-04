# overconfidence-prevention

The Flow's guardrail against under-asking. When in doubt, ask.

## The rule

Never infer past ambiguity. If a requirement, design decision, or acceptance
criterion is not completely clear, ask a clarifying question. Do not proceed to
the next stage while any unresolved ambiguity remains.

## Vague-answer flags

These phrases signal incomplete answers that must trigger a follow-up question:

- "mix of"
- "depends"
- "not sure"
- "somewhere between"
- "probably"
- "mostly"
- "typically"
- "generally"

If an answer contains any of these, the answer is incomplete. Ask a follow-up
that pins down the concrete choice: "depends on _what_?", "which specific case?",
"what is your assumption?"

## Comprehensive category coverage

For every decision point, verify coverage across:

- **Functional scope:** What exactly must the feature do? (Not: what might it do.)
- **Edge cases:** What happens when inputs are invalid, missing, or boundary?
- **Non-functional:** Performance, security, observability, accessibility constraints.
- **Integration points:** How does this connect to existing systems?
- **Failure modes:** What breaks this, and how does the system degrade?
- **User intent:** Why does the user need this? (Acceptance criteria alone may not capture it.)

If any category is missing or vague, write a clarifying question.

## The red flag

A non-trivial task reaching a checkpoint (Scope/publish, Shape/requirements,
Build/code-plan, Build/verify) with **zero clarifying questions asked** is a
structural red flag. It signals either:

- The task is genuinely trivial (confirm this explicitly).
- Ambiguity was silently inferred instead of surfaced and resolved.

If you observe this pattern, escalate: "No clarifying questions were asked
during [stage]. Is the scope truly unambiguous, or were assumptions made?"

## When this guide applies

This guide is invoked wherever the Flow asks questions: Scope/clarify,
Shape/requirements, Build/code-plan. It is a foundational check, not a
one-time gate.
