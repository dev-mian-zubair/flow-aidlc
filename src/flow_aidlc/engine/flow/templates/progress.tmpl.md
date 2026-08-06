# Progress — [Task ID]

> **Base branch:** origin/main
> <!-- The branch this workstream targets — branch-hardening + open-pr read this.
>      Default is your config.yaml → vcs.base; set to a sibling branch only for a
>      stacked epic child (ADR 0011). -->

Track each Flow stage for this task. Check off each stage as it completes.
Append one journal line to `journal.md` for every stage that closes.

## Scope

- [ ] clarify
- [ ] story
- [ ] publish

## Shape

- [ ] map-existing
- [ ] requirements
- [ ] design
- [ ] slicing

## Build

<!-- Repeat the four build stages for each slice. -->

### Slice [ID]: [Short title]

- [ ] slice-design
- [ ] code-plan
- [ ] generate
- [ ] verify

## Ship

- [ ] branch-hardening
- [ ] learnings
- [ ] open-pr

---

## Extension Configuration

Optional guardrails for this task. Set `enabled: true` to activate a guardrail
before the Build/verify stage. All `always_on` guardrails run regardless of
settings here. This block mirrors the `optional` list in `config.yaml` as
per-task enable toggles (the `enabled:` form here overrides the global default
for this task only).

```yaml
guardrails:
  always_on: []             # mirrors config.yaml → guardrails.always_on (the always_on set from config)
  optional:
    - name: security-baseline
      enabled: false
    - name: resiliency-baseline
      enabled: false
    - name: test-coverage
      enabled: false
    - name: dependency-provenance
      enabled: false
```

## Decision log (append-only)

<!-- YYYY-MM-DDTHH:MM:SSZ · <stage> · <decision> · <rationale> — see steps/shared/decision-log.md -->
