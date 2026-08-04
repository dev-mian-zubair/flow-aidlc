# Enable the resiliency-baseline guardrail for this task?

The RES guardrail enforces reliability patterns as blocking checks at Build/verify: explicit timeouts on every external call, idempotent retry operations, graceful degradation on dependency outages, and re-runnable background/queue tasks. Based on the AWS Well-Architected reliability pillar, directionally applied to your service boundaries.

A) Yes — enforce RES rules as blocking checks (recommended for any change that touches network calls, database writes, caches, object stores, background/queue tasks, or external integrations)
B) No — skip (fine for a throwaway prototype, or a task with no network / DB / queue surface)

[Answer]:
