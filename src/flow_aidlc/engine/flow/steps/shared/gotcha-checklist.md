# gotcha-checklist

At Shape/requirements, state the impact — or explicit `none` — of the proposed
change on **each of your project's always-on invariants**. One row per guardrail
listed under `guardrails.always_on` in `config.yaml`; every row must be filled
before the requirements checkpoint is approved.

A project with **no guardrails authored yet has an empty checklist** — that is
expected on a fresh repo. As you add always-on guardrails (see
`guardrails/always-on/README.md`), each one adds a row here.

A non-`none` impact means that guardrail **will** be enforced at Build/verify,
so plan for it now. Discovering a landmine at Build is expensive — shift left.

## How to fill the checklist

For each always-on guardrail in `config.yaml`, answer with one of:

- **`none`** — the change does not touch this concern at all.
- A short phrase describing the impact, e.g. *"adds a migration — must be
  additive"* or *"new endpoint — needs an authorization check"*.

Vague or empty answers are treated as incomplete by the checkpoint reviewer.

## The checklist

Build the table from `config.yaml → guardrails.always_on`: one row per enabled
guardrail, naming the invariant and linking to its file under
`../../guardrails/always-on/`. If the set is empty, the checklist is empty.

| Invariant | Guardrail file | Impact |
|-----------|----------------|--------|
| _(one row per guardrail in `config.yaml`; empty until you author guardrails)_ | | |

## Adopted from

The `aidlc-scoping` skill's "repo gotcha checklist", mapped to the Flow's
guardrails. The principle is the same: make every practitioner reckon with the
always-on invariants at requirements time, not after code is written.
