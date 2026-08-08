---
description: Approve the current checkpoint, mark the stage complete in progress.md, and advance per the playbook.
---

Read `.flow/playbook.md`, then read `worklog/<TICKET-ID>/progress.md` to identify the current checkpoint stage (the first unchecked `[ ]` that carries `checkpoint: yes` in the playbook); mark that stage `[x]` in `progress.md`; append a one-line approval entry to `worklog/<TICKET-ID>/journal.md` with the stage name and timestamp; then load the `load:` guide for the next stage in the playbook and begin it. Do not skip a checkpoint or advance past an unapproved one.
