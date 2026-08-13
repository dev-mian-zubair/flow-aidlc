---
description: Record a cross-cutting decision into the knowledge base at the current stage.
argument-hint: "<decision title or brief statement>"
---

Read `.flow/steps/shared/decision-format.md`, then create a new decision file in `docs/flow/knowledge/decisions/` using the template at `.flow/templates/decision.tmpl.md`, populated with `$ARGUMENTS` (the decision text), current task id, current stage (from `docs/flow/worklog/<TICKET-ID>/progress.md`), date, and any relevant context; append a one-line graduated-decision entry referencing the new file to `docs/flow/worklog/<TICKET-ID>/journal.md`; do not advance the workstream stage.
