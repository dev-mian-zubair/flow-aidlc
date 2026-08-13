---
description: Run Flow in auto mode — grind the flow-auto-labeled backlog autonomously (no checkpoints; adversarial panels gate each stage; merge on green CI). Terminal only when the queue is empty, a cap is hit, or .flow/STOP appears.
argument-hint: "[ticket e.g. ABC-123 — omit to grind the whole queue]"
---

Read `.flow/playbook.md` (the "Execution modes" section) and load `.flow/steps/auto/loop.md`, then run the autonomous loop.

**Preconditions (refuse if unmet):**
1. A CI workflow exists (`flow ci init`) — green CI is the auto-merge backstop. If absent, STOP and tell the user to run `flow ci init`.
2. `config.yaml → tracker` is configured with write scope (the loop pulls + comments on tickets).
If either fails, do not start; report what's missing.

**Invocation:**
- `/flow-auto` — grind every open ticket carrying the `execution.label` (default `flow-auto`) in priority order.
- `/flow-auto <id>` — run exactly one ticket autonomously.

**Non-negotiable:** auto mode runs every gate controlled mode runs; it only removes the human `/flow-approve` stops and adds the adversarial panels + merge-on-green-CI. Check `.flow/STOP` before each task and each stage — if present, stop gracefully after the current unit.
