---
description: Approve the current checkpoint, mark the stage complete in progress.md, and advance per the playbook.
---

Read `.flow/playbook.md` to orient to stage rules.

**Branch A — Worklog (Scope/Shape/Build/Ship) path (default):**
If there is an active worklog task (a `docs/flow/worklog/<TICKET-ID>/progress.md` whose stage checklist still has an unchecked `- [ ]` stage), identify the current checkpoint stage (the first unchecked `[ ]` that carries `checkpoint: yes` in the playbook); mark that stage `[x]` in `progress.md`; append a one-line approval entry to `docs/flow/worklog/<TICKET-ID>/journal.md` with the stage name and timestamp; then load the `load:` guide for the next stage in the playbook and begin it. Do not skip a checkpoint or advance past an unapproved one.

**Branch B — Discover (product-definition) path:**
If there is no active worklog task and a Discover run is in progress, resolve the active product unit — find `docs/flow/product/<slug>/progress.md` whose frontmatter is `status: in-discovery` (if several match, use the most-recently-modified). In that file's `## Stages` checklist, find the first unchecked `[ ]` gated stage (any stage where `checkpoint: yes` in the Discover table of the playbook), mark it `[x]` (the `progress.md` checkbox is the record — Discover units have no journal), then load the `load:` guide for the next Discover stage in the playbook and begin it. Do not skip a checkpoint or advance past an unapproved one.
