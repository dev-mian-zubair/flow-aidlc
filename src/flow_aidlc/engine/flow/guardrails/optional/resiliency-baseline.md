# Resiliency Baseline

**ID prefix:** RES · **Enforcement:** opt-in (blocking when enabled)

## Rule

New network, database, and queue interactions are resilient. Every external call has an explicit timeout; retried operations are idempotent; failures degrade gracefully without crashing the service on a dependency outage; background/queue tasks are safe to re-run. (Directional reliability guidance.)

## Verification

- **RES-01** Explicit timeouts: every new call to an external service (HTTP, database, cache, object store, or any network dependency) sets an explicit `timeout` or uses a client configured with one; no unbounded blocking call is introduced.
- **RES-02** Idempotent retries: any operation under a retry policy (framework retry decorator or a manual retry loop) produces the same end state on re-execution; side-effecting operations (writes, sends) are guarded by an idempotency key or an existence check before acting.
- **RES-03** Graceful degradation: new code that calls an optional dependency catches the relevant exception classes and returns a degraded-but-valid response rather than propagating an unhandled crash to the caller.
- **RES-04** Re-runnable background tasks: new background/queue tasks do not assume single-execution semantics; they handle duplicate delivery (check-before-write, upsert, or idempotency key) and do not leave partial state on failure that prevents a clean retry.

## Blocks on

- An unbounded external call with no timeout.
- A non-idempotent operation inside a retry loop.
- a dependency outage that crashes rather than degrades gracefully (RES-03)
- a background/queue task that is not safe to re-run (RES-04)

## Powered by superpowers

Runs at Build/verify via the `guardrail-verifier`. A suspected non-idempotent or unbounded path is traced with `superpowers:systematic-debugging` before the checkpoint is cleared.
