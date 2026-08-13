---
description: Manually start the next Build slice — slice-design → code-plan → generate → verify.
argument-hint: "<slice name or number (optional)>"
---

Read `.flow/playbook.md`, then read `docs/flow/worklog/<TICKET-ID>/shape/slices.md` and pick the target slice — if `$ARGUMENTS` names a slice (by name or number) use that, otherwise take the next unstarted slice; enter the Build loop for that slice by loading `.flow/steps/build/slice-design.md`, then `.flow/steps/build/code-plan.md` (dispatching the read-only `checkpoint-reviewer` to verify the plan, then pausing at the `code-plan` checkpoint for `/flow-approve`), then `.flow/steps/build/generate.md` (invoking `superpowers:test-driven-development`), and finally `.flow/steps/build/verify.md` (invoking `superpowers:requesting-code-review` and `superpowers:verification-before-completion`, dispatching the `guardrail-verifier` subagent and then the read-only `checkpoint-reviewer`, and pausing at the `verify` checkpoint for `/flow-approve`). This command is the conductor — it owns every subagent dispatch; the Build stage agents are leaves.
