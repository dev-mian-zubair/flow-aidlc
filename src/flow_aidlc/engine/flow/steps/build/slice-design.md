# slice-design

Enter this stage once per build slice, after `steps/shape/slicing.md` assigns the slice id and scope.

## Goal

Produce a concrete design document for the slice — precise enough that code-plan can generate a
checkboxed file list without re-reading the codebase.

## Inputs

- `docs/flow/worklog/<TICKET-ID>/shape/slices.md` — the slice entry (id, scope, files, requirement refs).
- `docs/flow/worklog/<TICKET-ID>/shape/design.md` — component-level decisions from Shape.
- Any relevant ADRs under `docs/adr/`.

## Steps

1. **Read** the slice entry in `slices.md`. Note the scope boundary — writes are confined to the
   listed files; do not expand scope here.
2. **Draft `docs/flow/worklog/<TICKET-ID>/build/<slice-id>/design.md`** with these sections:
   - **Signatures** — every new or changed function/class/type, with argument names and return types.
   - **Logic** — step-by-step description of each non-trivial behaviour.
   - **Edge cases** — exhaustive list; note which ones need explicit test coverage.
   - **Data contracts** — request/response schemas, DB column changes, event payloads.
   - **Cross-cutting concerns** — authz checks, migration safety, budget integrity (flag if any
     `always_on` guardrail is relevant to this slice).
3. **Stop** if any ambiguity cannot be resolved from existing docs. Raise a question in
   `docs/flow/worklog/<TICKET-ID>/journal.md` and wait for a human answer before continuing.
4. Save the document. Proceed to `steps/build/code-plan.md`.

## Output

`docs/flow/worklog/<TICKET-ID>/build/<slice-id>/design.md` — populated, no `[Answer]:` placeholders remaining.
