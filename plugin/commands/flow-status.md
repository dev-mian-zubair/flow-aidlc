---
description: Print the current stage progress, open questions, and any stale docs for the active workstream.
argument-hint: "<ticket e.g. ABC-123>"
---

Resolve `<TICKET-ID>` from `$ARGUMENTS` (ask the user if not provided). Read `.flow/playbook.md`, then read `docs/flow/worklog/<TICKET-ID>/progress.md` and print a summary of completed stages (checked `[x]`) and the current stage (first unchecked `[ ]`); list any open question files found under `docs/flow/worklog/<TICKET-ID>/questions/`; scan `docs/flow/worklog/<TICKET-ID>/journal.md` for unresolved blocker entries; and flag any `docs/flow/worklog/<TICKET-ID>/shape/` or `docs/flow/worklog/<TICKET-ID>/build/` artifacts whose modification time predates the last journal entry, indicating they may be stale. Do not modify any files.
