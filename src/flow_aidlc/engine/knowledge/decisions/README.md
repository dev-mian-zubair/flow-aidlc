# Decision Records

This directory holds the founding Architecture Decision Records (ADRs) for the
Perpetual Intelligence Platform and its Flow operating methodology.

## Index

| # | Title | Status | Date |
|---|-------|--------|------|
| [0001](0001-adopt-flow.md) | Adopt Flow | accepted | 2026-08-03 |
| [0002](0002-self-updating-knowledge.md) | Self-Updating Knowledge | accepted | 2026-08-03 |
| [0003](0003-worklog-committed.md) | Worklog Committed | accepted | 2026-08-03 |
| [0004](0004-coordination-absorbed-into-flow.md) | Coordination Absorbed into the Flow | accepted | 2026-08-04 |
| [0005](0005-adopt-aidlc-eval-and-guidance.md) | Adopt AWS AI-DLC eval + guidance mechanisms | accepted | 2026-08-04 |
| [0006](0006-adopt-learnings-and-traceability.md) | Adopt learnings loop + traceability verification | accepted | 2026-08-04 |
| [0007](0007-blend-aidlc-scoping.md) | Blend aidlc-scoping into the Flow | accepted | 2026-08-04 |

## Immutability Rule

ADRs are **immutable**. Once accepted, a record is never edited or deleted.
If a decision is reversed or superseded, create a new record with the higher
number and mark the old one `superseded by MMMM`. This preserves the full
reasoning trail for auditors and future developers.

Rationale: the value of an ADR is knowing what was true at the time it was
written. Rewriting history destroys that value.
