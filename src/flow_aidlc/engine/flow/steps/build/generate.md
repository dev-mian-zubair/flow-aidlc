# generate

Powered by superpowers — invokes `superpowers:test-driven-development`.

## Goal

Implement the slice by working through the approved code plan, test-first, writing all code to
the workspace. Nothing is written to `worklog/`.

## Inputs

- `worklog/<PI-NNN>/build/<slice-id>/code-plan.md` — approved, all checkboxes unchecked.
- `worklog/<PI-NNN>/build/<slice-id>/design.md` — signatures and edge cases.

## Scope guard

Writes are fenced to the files listed in `slices.md` for this slice id. Before creating or
modifying any file:

1. Confirm the file path appears in the slice's file list.
2. If it does not, stop and raise a scope-creep flag in `journal.md`. Do not write the file.

## Steps

1. **Invoke `superpowers:test-driven-development`** at the start of this stage. Follow the
   TDD cycle it prescribes: write a failing test → implement the minimum code to pass → refactor.
2. Work through `code-plan.md` **top to bottom**, one checkbox at a time:
   a. Write (or update) the test for the change described by the checkbox.
   b. Run the test suite to confirm the new test fails as expected.
   c. Implement the change in the workspace file.
   d. Run the test suite to confirm the new test passes and no existing tests regress.
   e. Check off the checkbox in `code-plan.md`.
3. After all checkboxes are checked, run your project's test command one final
   time (`config.yaml` → `commands.test`; e.g. `make test`, `npm test`, or `pytest`).
4. All tests must be green before leaving this stage. A red suite blocks entry to `verify.md`.

## Output

- All workspace files modified or created per the plan.
- `worklog/<PI-NNN>/build/<slice-id>/code-plan.md` — all checkboxes checked.
- Test suite green.

Proceed to `steps/build/verify.md`.
