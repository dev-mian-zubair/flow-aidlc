---
description: Record a cross-cutting decision into the knowledge base at the current stage.
argument-hint: "<decision title or brief statement>"
---

Read `.flow/steps/shared/decision-format.md`, then create a new decision file in `knowledge/decisions/` using the template at `.flow/templates/decision.tmpl.md`, populated with the provided decision text, current task id, current stage (from `worklog/<PI-NNN>/progress.md`), date, and any relevant context; append a one-line graduated-decision entry referencing the new file to `worklog/<PI-NNN>/journal.md`; do not advance the workstream stage.
