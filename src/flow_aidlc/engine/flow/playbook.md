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

## Per-Stage Table

| Phase | Stage | When | load: | skill: | checkpoint: |
|-------|-------|------|-------|--------|-------------|
| Scope | clarify | ALWAYS | `steps/scope/clarify.md` | `superpowers:brainstorming` | no |
| Scope | story | ALWAYS | `steps/scope/story.md` | — | no |
| Scope | publish | ALWAYS | `steps/scope/publish.md` | — | yes (outward-write approval) |
| Shape | map-existing | CONDITIONAL: brownfield | `steps/shape/map-existing.md` | — | no |
| Shape | requirements | ALWAYS | `steps/shape/requirements.md` | `superpowers:brainstorming` | yes |
| Shape | design | ALWAYS | `steps/shape/design.md` | — | yes |
| Shape | slicing | ALWAYS | `steps/shape/slicing.md` | — | no |
| Build | slice-design | ALWAYS | `steps/build/slice-design.md` | — | no |
| Build | code-plan | ALWAYS | `steps/build/code-plan.md` | — | yes |
| Build | generate | ALWAYS | `steps/build/generate.md` | `superpowers:test-driven-development` | no |
| Build | verify | ALWAYS | `steps/build/verify.md` | `superpowers:requesting-code-review` + `superpowers:verification-before-completion` | yes |
| Ship | release-checklist | ALWAYS | `steps/ship/release-checklist.md` | `superpowers:finishing-a-development-branch` | yes |
| Ship  | learnings | ALWAYS | `steps/ship/learnings.md` | — | no |
| Ship | handoff | ALWAYS | `steps/ship/handoff.md` | — | no |

> **Scope classification.** `clarify` also classifies the idea as `bug | task |
> feat | epic` (confirmed with the user) and, for an epic, decomposes it into
> one-level child stubs. `story` then fills the matching `templates/scope/*`
> template(s), and `publish` creates a single issue or an Epic parent + child
> sub-issues linked via the tracker's sub-issue mechanism.

## Checkpoint Rule

At each stage where `checkpoint: yes`, **stop and wait for `/flow-approve`** before advancing to the next stage. The `checkpoint-stop` hook enforces this automatically. Do not proceed past a checkpoint under any circumstance without explicit approval.

## Guardrail Loading

At the **Build/verify** stage:

1. Read `config.yaml` and collect all entries under `guardrails.always_on` and any enabled entries under `guardrails.optional`.
2. Load and run each enabled guardrail check before the verify stage completes.
3. **Block on any failure** — a guardrail failure must be resolved before the checkpoint at Build/verify can be approved.

Current guardrails (from `config.yaml`):

- **always_on:** whatever your `config.yaml` lists — empty until you author guardrails for your project's invariants (see `guardrails/always-on/README.md`).
- **optional:** `security-baseline`, `resiliency-baseline`, `test-coverage`

## State Tracking

- As each stage completes, update the checkbox for that stage in `worklog/<task>/progress.md`.
- Append a one-line entry to `journal.md` recording the stage name, outcome, and timestamp.
- At each checkpoint outcome (approved, skipped, discrepancy, or handoff), also append one `steps/shared/decision-log.md` line to the `## Decision log` section in `progress.md`.
