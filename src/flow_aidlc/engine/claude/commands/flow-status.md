---
description: Print the current stage progress, open questions, and any stale docs for the active workstream.
argument-hint: "<ticket e.g. ABC-123>"
---

Read `.flow/playbook.md`, then read `worklog/<TICKET-ID>/progress.md` and print a summary of completed stages (checked `[x]`) and the current stage (first unchecked `[ ]`); list any open question files found under `worklog/<TICKET-ID>/questions/`; scan `worklog/<TICKET-ID>/journal.md` for unresolved blocker entries; and flag any `worklog/<TICKET-ID>/shape/` or `worklog/<TICKET-ID>/build/` artifacts whose modification time predates the last journal entry, indicating they may be stale. Do not modify any files.
