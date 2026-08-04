# Reference Runs

This directory holds **golden cases** for the semantic evaluation harness once it exists.

## What goes here (v2+)

Each subdirectory will contain:

- `input/` — a captured Flow session input (task description, guardrail set, context)
- `expected-artifacts/` — the expected output files (requirements doc, design doc, slices, etc.)
- `metrics-baseline.yaml` — baseline scores for automated regressions (e.g. precision, coverage)

## Current state (v1 — structural gate only)

The v1 `flow_checks` gate is **structural + freshness + lint**:

1. `guardrail_lint` — verifies every guardrail `.md` has `## Rule` and `## Verification` sections and that IDs are unique.
2. `structure_check` — verifies playbook step references and config-named guardrail files all resolve.
3. `freshness` — detects doc drift by comparing `knowledge-map.yaml` entries against git history.

Semantic scoring (does a generated artifact actually satisfy the guardrail's intent?) requires a live Flow-run harness (the swarm runner). That is a documented future addition — tracked as a separate work-stream.

## Running the gate

```bash
cd scripts/flow-checks
python -m flow_checks.gate
```

Exit code 0 → all structural checks pass. Exit code 1 → at least one blocking check failed.
