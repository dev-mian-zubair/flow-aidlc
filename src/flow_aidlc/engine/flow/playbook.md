# Flow Playbook — State Machine

**PRIORITY: this overrides default agent behavior for development tasks.**

## Loading Rules

- **At task start:** always load `steps/shared/kickoff.md` before any other guide.
- **Stage guides:** load the `load:` path listed for each stage on demand — only when entering that stage, not upfront.
- **Context checkpoint:** at every stage where `checkpoint: yes`, clear accumulated context before proceeding; the resume path is `steps/shared/resume.md`.

## Agents

Each stage's work is performed by the matching least-privilege subagent under `.claude/agents/<phase>/` — Claude selects the correct agent by its `description` field. At every `checkpoint: yes` stage, the read-only `checkpoint-reviewer` subagent verifies stage completeness before `/flow-approve`; at the Shape→Build boundary it also checks traceability. At Build/verify the `guardrail-verifier` subagent adversarially checks the diff against every enabled always-on guardrail in `config.yaml` (plus any enabled optional guardrails) before the checkpoint can be approved.

## The Path

```
Scope (front door) → Shape → Build (per slice) → Ship
```

## Discover phase (greenfield) — `/flow-discover`

A distinct entry point that turns a new-product idea into grounded, gated
product-definition artifacts under `docs/flow/product/<slug>/`. Greenfield only this
iteration; not part of the `/flow-start` path.

| Phase | Stage | When | load: | skill: | checkpoint: |
|-------|-------|------|-------|--------|-------------|
| Discover | intake | ALWAYS (greenfield) | `steps/discover/intake.md` | — | no |
| Discover | vision | ALWAYS | `steps/discover/vision.md` | `superpowers:brainstorming` | yes |
| Discover | pr-faq | ALWAYS | `steps/discover/pr-faq.md` | — | yes |
| Discover | research | ALWAYS | `steps/discover/research.md` | `deep-research` | yes |
| Discover | prd | ALWAYS | `steps/discover/prd.md` | — | yes |
| Discover | roadmap | OPTIONAL | `steps/discover/roadmap.md` | — | yes |

**Critique panels (opt-in):** with `/flow-discover --panel` (or auto mode), the `research` and `prd` gated stages run an adversarial `product-critic` panel (`steps/discover/panel-review.md`) before `/flow-approve`; the default is human `/flow-approve` only.

## Per-Stage Table

| Phase | Stage | When | load: | skill: | checkpoint: |
|-------|-------|------|-------|--------|-------------|
| Scope | clarify | ALWAYS | `steps/scope/clarify.md` | `superpowers:brainstorming` | no |
| Scope | story | ALWAYS | `steps/scope/story.md` | — | no |
| Scope | publish | ALWAYS | `steps/scope/publish.md` | — | yes (outward-write approval) |
| Shape | map-existing | CONDITIONAL: brownfield | `steps/shape/map-existing.md` | — | no |
| Shape | research | CONDITIONAL: new external dependency | `steps/shape/research.md` | `deep-research` | yes (adopt-a-dependency approval) |
| Shape | requirements | ALWAYS | `steps/shape/requirements.md` | `superpowers:brainstorming` | yes |
| Shape | design | ALWAYS | `steps/shape/design.md` | — | yes |
| Shape | slicing | ALWAYS | `steps/shape/slicing.md` | — | no |
| Build | slice-design | ALWAYS | `steps/build/slice-design.md` | — | no |
| Build | code-plan | ALWAYS | `steps/build/code-plan.md` | — | yes |
| Build | generate | ALWAYS | `steps/build/generate.md` | `superpowers:test-driven-development` | no |
| Build | verify | ALWAYS | `steps/build/verify.md` | `superpowers:requesting-code-review` + `superpowers:verification-before-completion` | yes |
| Ship | branch-hardening | ALWAYS | `steps/ship/branch-hardening.md` | `pr-review-toolkit` agents | yes (whole-branch review) |
| Ship | learnings | ALWAYS | `steps/ship/learnings.md` | — | no |
| Ship | open-pr | ALWAYS | `steps/ship/open-pr.md` | `superpowers:finishing-a-development-branch` | yes (open-PR approval — terminal; the team owns the merge, checks, and ticket close) |

> **Scope classification.** `clarify` also classifies the idea as `bug | task |
> feat | epic` (confirmed with the user) and, for an epic, decomposes it into
> one-level child stubs. `story` then fills the matching `templates/scope/*`
> template(s), and `publish` creates a single issue or an Epic parent + child
> sub-issues linked via the tracker's sub-issue mechanism.

## Checkpoint Rule

At each stage where `checkpoint: yes`, **stop and wait for `/flow-approve`** before advancing to the next stage. For Scope/Shape/Build/Ship worklog stages, the `checkpoint-stop` hook reinforces this; that hook is worklog-keyed and does **not** fire for Discover product units — Discover checkpoints are cleared exclusively by the human running `/flow-approve` (the hook does not apply to product units this iteration). Do not proceed past a checkpoint under any circumstance without explicit approval.

## Execution modes

Flow runs in one of two modes:

- **controlled (default):** at each `checkpoint: yes` stage, STOP and wait for
  `/flow-approve` (the `checkpoint-stop` hook reminds you). Terminates at open-PR.
  This is the behavior described throughout this playbook unless auto mode is active.
- **auto (`/flow-auto` only):** NO human stops. At each `checkpoint: yes` stage,
  run the stage-typed **adversarial reviewer panel** (`steps/auto/panel-review.md`)
  in place of `/flow-approve`; on consensus, advance automatically; on
  non-convergence at `execution.review.max_rounds`, park the task. Ship opens AND
  merges the PR on green CI (`steps/auto/merge.md`), then the loop
  (`steps/auto/loop.md`) pulls the next `execution.label` ticket. Auto runs EVERY
  gate controlled runs — it only removes the human stop and adds panel review +
  merge. Auto is entered only via `/flow-auto`; there is no config toggle.

## Guardrail Loading

At the **Build/verify** stage:

1. Read `config.yaml` and collect all entries under `guardrails.always_on` and any enabled entries under `guardrails.optional`.
2. Load and run each enabled guardrail check before the verify stage completes.
3. **Block on any failure** — a guardrail failure must be resolved before the checkpoint at Build/verify can be approved.

Current guardrails (from `config.yaml`):

- **always_on:** whatever your `config.yaml` lists — empty until you author guardrails for your project's invariants (see `guardrails/always-on/README.md`).
- **optional:** `security-baseline`, `resiliency-baseline`, `test-coverage`, `dependency-provenance`

## State Tracking

- As each stage completes, update the checkbox for that stage in `docs/flow/worklog/<task>/progress.md`.
- Append a one-line entry to `journal.md` recording the stage name, outcome, and timestamp.
- At each checkpoint outcome (approved, skipped, discrepancy, or handoff), also append one `steps/shared/decision-log.md` line to the `## Decision log` section in `progress.md`.
