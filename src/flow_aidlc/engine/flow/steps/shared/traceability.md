# traceability

Traceability ensures every requirement is verified by at least one slice.

## Requirement IDs

Functional and non-functional requirements are tagged with stable IDs:

- **FR-N** — Functional requirement (e.g. `FR-1`, `FR-2`)
- **NFR-N** — Non-functional requirement (e.g. `NFR-1`, `NFR-2`)

These IDs are assigned in the `requirements.md` document and cited in each
slice's `Requirement refs` field.

## Traceability matrix

The Shape stage emits a traceability matrix as
`worklog/<TICKET-ID>/shape/traceability.md`. This document lists every FR/NFR and
which slices cover it (a requirement→slice cross-reference).

## Coverage rule

- **Every FR/NFR must be cited by at least one slice.** An uncovered requirement
  blocks advancement from Shape to Build.
- A slice citing an unknown requirement ID is a warning — it suggests either a
  typo in the ID or a mismatch between `requirements.md` and `slices.md`.

## Running the check

To generate the traceability matrix and validate coverage:

```bash
python -m flow_aidlc.checks.traceability worklog/<TICKET-ID> --write
```

This command:

1. Parses all FR/NFR IDs from `worklog/<TICKET-ID>/shape/requirements.md`.
2. Parses all `Requirement refs` from `worklog/<TICKET-ID>/shape/slices.md`.
3. Generates `worklog/<TICKET-ID>/shape/traceability.md` with the matrix.
4. Reports any uncovered requirements (error) or unknown requirement IDs
   (warning).
5. Exits with a non-zero status if any error is found.

Fix any uncovered requirements by adding them to at least one slice's `Requirement refs`.
