---
description: Resume a workstream after a context reset by rebuilding state from the worklog.
argument-hint: "<ticket e.g. ABC-123>"
---

Load `.flow/steps/shared/resume.md` and follow it exactly: identify the task id from the argument (ask if not provided), read `worklog/<TICKET-ID>/progress.md` to find the first unchecked checkpoint, look up that stage in `.flow/playbook.md` to find its `load:` path, read the stage guide and its dependency artifacts, read the journal tail from `worklog/<TICKET-ID>/journal.md`, announce "Resumed: <TICKET-ID>  Current stage: <stage name>", then continue from that stage as if it is just starting.
