---
description: Enter the Ship phase — run the release checklist, then learnings retro, then handoff.
---

Read `.flow/playbook.md`, then verify that all Build slices in `worklog/<PI-NNN>/shape/slices.md` are checked complete in `worklog/<PI-NNN>/progress.md` before proceeding; enter the Ship phase by loading `.flow/steps/ship/branch-hardening.md` first (dispatching the `pr-review-toolkit` agents from `config.yaml → review.branch_hardening` on the branch diff) and pausing at the `branch-hardening` checkpoint for `/flow-approve`; upon approval load `.flow/steps/ship/release-checklist.md` (invoking `superpowers:finishing-a-development-branch`) and pausing at the `release-checklist` checkpoint for `/flow-approve`; upon approval load `.flow/steps/ship/learnings.md` (the learnings retro) and complete it; then load `.flow/steps/ship/handoff.md` and complete the handoff; append final entries to `worklog/<PI-NNN>/journal.md`.
