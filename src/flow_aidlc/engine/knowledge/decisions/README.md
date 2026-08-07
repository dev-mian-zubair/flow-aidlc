# Decision Records

This directory holds your project's Architecture Decision Records (ADRs) — the
durable reasoning trail behind the choices that shape this codebase and its Flow
operating methodology.

## Index

_No decision records yet._ Add one as `NNNN-short-title.md` (zero-padded,
sequential) and list it in the table below.

| # | Title | Status | Date |
|---|-------|--------|------|
| _(none)_ | | | |

## Immutability Rule

ADRs are **immutable**. Once accepted, a record is never edited or deleted.
If a decision is reversed or superseded, create a new record with the higher
number and mark the old one `superseded by MMMM`. This preserves the full
reasoning trail for auditors and future developers.

Rationale: the value of an ADR is knowing what was true at the time it was
written. Rewriting history destroys that value.
