# Progress — [Task ID]

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
- [ ] release-checklist
- [ ] learnings
- [ ] handoff

---

## Extension Configuration

Optional guardrails for this task. Set `enabled: true` to activate a guardrail
before the Build/verify stage. All `always_on` guardrails run regardless of
settings here. This block mirrors the `optional` list in `config.yaml` as
per-task enable toggles (the `enabled:` form here overrides the global default
for this task only).

```yaml
guardrails:
  always_on:
    - migration-safety      # enabled: always
    - budget-integrity      # enabled: always
    - authz-completeness    # enabled: always
    - router-safety         # enabled: always
    - license-sku-gating    # enabled: always
  optional:
    - name: security-baseline
      enabled: false
    - name: resiliency-baseline
      enabled: false
    - name: test-coverage
      enabled: false
```

## Decision log (append-only)

<!-- YYYY-MM-DDTHH:MM:SSZ · <stage> · <decision> · <rationale> — see steps/shared/decision-log.md -->
