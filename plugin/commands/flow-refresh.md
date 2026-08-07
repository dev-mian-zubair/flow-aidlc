---
description: Dispatch the curator subagent to verify knowledge/map/ invariants against current code (structure lives in the code graph).
---

Read `.flow/playbook.md`, then dispatch the `curator` subagent to review `knowledge/map/`: verify each map's **invariants** still hold against the current code — reading source and, for structure, the code graph via `mcp__graphify` (structure lives in the graph, not in prose) — correcting any invariant that has drifted and confirming each doc's `enforced-by:` guardrail resolves. Upon completion print a summary of which docs were updated and which were already accurate. Do not modify worklog or progress files.
