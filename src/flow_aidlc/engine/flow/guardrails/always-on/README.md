# Always-on guardrails

This directory holds **your project's blocking invariants** — the rules that
must hold on every change, checked by the `guardrail-verifier` agent at
Build/verify. It ships **empty**: a fresh project has no invariants yet, and a
guardrail is only useful when it cites real code in *your* repo.

## What an always-on guardrail is

An always-on guardrail is a short markdown file encoding one invariant your
codebase must never violate — e.g. "every new endpoint has an authorization
check", "database migrations are additive-only", "money is only written through
the ledger". Each guardrail:

- Declares an **ID prefix** and numbered rules (`<PREFIX>-01`, `<PREFIX>-02`, …).
- States a **mechanical Verification** procedure the verifier can run
  (a `grep`, a test, a file check) — grounded in **real paths in your repo**.
- Lists what it **Blocks on**.
- Is enforced only when its filename (minus `.md`) is listed under
  `guardrails.always_on` in `.flow/config.yaml`.

At Build/verify, `guardrail-verifier` loads the enabled set from
`config.yaml`, reads each file here, and checks the diff against every rule.
There is no hardcoded guardrail list — the config is the source of truth.

## Authoring one

1. `flow guardrail add <name>` scaffolds `always-on/<name>.md` from
   `TEMPLATE.md` and appends `<name>` to `guardrails.always_on` in
   `config.yaml`.
2. Fill every `[FILL]` placeholder — especially the Verification steps, which
   must reference concrete files/patterns in your repository so the check is
   mechanical, not aspirational.
3. Author one guardrail **per invariant**; keep each file focused on a single
   concern.

Optional, project-agnostic starters (security / resiliency / test-coverage)
live in `../optional/` and are enabled per-task rather than always-on.
