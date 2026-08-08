# Authorization on Mutations

**ID prefix:** AUTHZ · **Enforcement:** blocking when enabled

## Rule

Every state-changing operation (create/update/delete endpoint, mutation resolver, queue/command handler) enforces an explicit authorization check before it acts. Authorization is deny-by-default: a handler that reaches its side effect without having established the caller's permission is a defect, even if a gateway "usually" guards it.

## Verification

- **AUTHZ-01** Explicit check present: every new or modified mutating handler performs an authorization check (role/permission/ownership) before the write, referencing the caller's identity — not merely authentication (who) but authorization (may they).
- **AUTHZ-02** Deny-by-default: the check fails closed — an unrecognized role, missing scope, or unresolved owner denies the operation rather than falling through to success.
- **AUTHZ-03** Object-level ownership: for operations on a specific resource, the handler verifies the caller may act on *that* resource (ownership/tenancy), not just that they hold the action's permission in general.

## Blocks on

- A new mutating endpoint/handler with no authorization check before its side effect.
- An authorization branch that fails open (unknown role → allowed).
- A resource mutation that checks the permission but not ownership of the specific object (AUTHZ-03).

## Powered by superpowers

Runs at Build/verify via the `guardrail-verifier`. A suspected missing or fail-open check is traced with `superpowers:systematic-debugging` before the checkpoint is cleared.
