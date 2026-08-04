# Practices

Curated, revisable working practices distilled from completed tasks by the
Ship-time learnings retro (steps/ship/learnings.md). Unlike knowledge/decisions/
(immutable ADRs about specific architectural choices), practices are revisable
methodology guidance. Loaded at kickoff so every task benefits. Each carries an
idempotency marker so the retro never duplicates one.

## P-1 — Verify documented commands by executing them
<!-- practice-marker: verify-documented-commands-by-executing-them -->

**Practice:** When a doc or README shows a command, run it during review — don't
just read it. A reproducibility harness shipped with a self-consistency command
that silently FAILed because a path was wrong.
**Why:** Documented-but-broken commands read as working; only execution catches them.
**Source:** PI-WS10
