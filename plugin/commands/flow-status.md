---
description: Print the current stage progress, open questions, and any stale docs for the active workstream.
argument-hint: "<ticket e.g. PI-123>"
---

Read `.flow/playbook.md`, then read `worklog/<PI-NNN>/progress.md` and print a summary of completed stages (checked `[x]`) and the current stage (first unchecked `[ ]`); list any open question files found under `worklog/<PI-NNN>/questions/`; scan `worklog/<PI-NNN>/journal.md` for unresolved blocker entries; and flag any `worklog/<PI-NNN>/shape/` or `worklog/<PI-NNN>/build/` artifacts whose modification time predates the last journal entry, indicating they may be stale. Do not modify any files.
