---
description: Dispatch the curator subagent to re-derive stale knowledge/map/ docs from current code.
---

Read `.flow/playbook.md`, then dispatch the `curator` subagent to scan `knowledge/map/` for documents whose content is stale relative to the current codebase; the curator will re-derive each stale doc from current code using Read, Grep, Glob, Write, and Edit as needed; upon completion print a summary of which docs were refreshed and which were already current. Do not modify worklog or progress files.
