---
description: Begin a new workstream for a scoped ticket — scaffold worklog, then run Shape.
argument-hint: "<ticket e.g. ABC-123>"
---

**Ticket precondition — Shape needs a real, tracker-created ticket.** Before scaffolding anything, resolve a confirmed ticket id:

- **A ticket id was provided** (`<TICKET-ID>` / tracker issue number) → dispatch `shape-intake`, which **verifies the id exists in the tracker**. If it exists, proceed to Shape (below). If it does **not** exist, treat it as "no ticket."
- **No ticket id, or the provided id doesn't exist** → do **not** scaffold a worklog. Ask the user, conversationally: *"What's the ticket number for this work? If you don't have one yet, I'll create it first via Scope."*
  - The user supplies a valid existing id → verify it (as above), then proceed.
  - The user has no ticket → **chain into `/flow-scope`** to create one. Scope runs its own front door (clarify → story → publish **checkpoint**) and creates the ticket **only after the user's `/flow-approve`** — that outward-write gate is never bypassed. Once Scope returns a `<TICKET-ID>`, resume this command with that id.

Then, for a **confirmed** ticket id: read `.flow/playbook.md`. `shape-intake` (dispatched above) runs `.flow/steps/shared/kickoff.md` — it creates the task branch, scaffolds `docs/flow/worklog/<TICKET-ID>/`, announces the task **once**, and returns a `ROUTE`. Do **not** repeat the scaffold or announce here. Following that `ROUTE`, proceed through the Shape stages in sequence — the conditional pre-steps `.flow/steps/shape/map-existing.md` (brownfield work) and `.flow/steps/shape/research.md` (when the feature needs a new external dependency the stack lacks), then `.flow/steps/shape/requirements.md` (invoking `superpowers:brainstorming`), `.flow/steps/shape/design.md`, and `.flow/steps/shape/slicing.md`. At each checkpoint stage (`research`, `requirements`, `design`), after the stage's artifact is produced, **dispatch the read-only `checkpoint-reviewer`** to verify completeness (and traceability at the Shape→Build boundary), then pause for `/flow-approve` before advancing. The stage agents are leaf agents — the conductor (this command) owns every subagent dispatch.
