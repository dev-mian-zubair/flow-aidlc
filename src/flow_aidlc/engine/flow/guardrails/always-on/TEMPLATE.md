# [FILL: Guardrail Name]

**ID prefix:** [FILL: 3–4 uppercase letters, e.g. AUTH] · **Enforcement:** always-on (blocking)

## Rule

[FILL: state the invariant in one or two sentences. What must always hold true
on every change? Write it as a property of the code, not a wish — e.g. "Every
new HTTP endpoint enforces an authorization check before returning data."]

## Verification

Number each check `<PREFIX>-NN`. Each must be **mechanical** — something the
`guardrail-verifier` can run read-only against the diff (a `grep`, a test, a
file/AST check) — and must cite **real paths in this repository**.

- **[PREFIX]-01** [FILL: mechanical check + the concrete file(s)/pattern it
  inspects, e.g. "every new route in `src/api/**` has a `@requires_auth`
  decorator; grep the diff for new `@router.<verb>` without an auth dependency
  → zero hits."]
- **[PREFIX]-02** [FILL: second check, grounded in a real path.]
- **[PREFIX]-03** [FILL: optional further check.]

## Blocks on

- [FILL: the specific condition that fails the check, e.g. "A new endpoint with
  no authorization gate."]
- [FILL: another blocking condition.]

## Powered by superpowers

Runs at Build/verify via the `guardrail-verifier`. [FILL: name the superpowers
skill used when a finding's root cause is ambiguous, e.g. "A flagged finding
whose cause is unclear is diagnosed with `superpowers:systematic-debugging`
before the checkpoint is cleared."]
