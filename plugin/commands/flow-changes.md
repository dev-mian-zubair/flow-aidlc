---
description: Record a change request at the current checkpoint without advancing the workstream.
argument-hint: "<description of the requested change>"
---

Read `.flow/playbook.md`, then read `docs/flow/worklog/<TICKET-ID>/progress.md` to identify the current stage; append the change request (`$ARGUMENTS`) as a timestamped entry to `docs/flow/worklog/<TICKET-ID>/journal.md` under a `## Change Request` heading that records the stage, the request text, and the timestamp; do NOT mark the current stage complete and do NOT advance to the next stage — the workstream stays at the current checkpoint until `/flow-approve` is issued after the changes are addressed.
