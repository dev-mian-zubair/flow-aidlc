# Dependency Provenance

**ID prefix:** DEP · **Enforcement:** optional (blocking when enabled)

> A project may **promote** this to always-on: list `dependency-provenance` under
> `guardrails.always_on` in `config.yaml` (and move this file to
> `guardrails/always-on/`) so the guardrail-verifier enforces it on every slice.

## Rule

Every external dependency **newly added** in the diff must trace to an **approved
research ADR** (`docs/flow/knowledge/decisions/`) produced by Shape / research. What Build
installs must equal what the governance screen reviewed and approved — no
unreviewed, substituted, or extra dependencies.

## Verification

- **DEP-01** (detect new deps): identify dependencies added in the slice diff —
  new/changed entries in your project's dependency manifests + lockfiles (e.g.
  `package.json`, `requirements*.txt`, `pyproject.toml`, `go.mod`, `Cargo.toml`).
  (Mechanical: `git diff` the manifests; collect added package names.) If none
  were added, the guardrail is **N/A** for this slice.
- **DEP-02** (ADR exists): for each newly-added top-level dependency, an approved
  ADR under `docs/flow/knowledge/decisions/` (or this task's
  `docs/flow/worklog/<ID>-NNN/shape/research.md`) names that exact package as the adopted
  dependency.
- **DEP-03** (matches the approved package): the installed package name — and,
  where the ADR pins it, the major version / source registry — matches the ADR,
  not a different library serving the same purpose.
- **DEP-04** (governance screen cleared): the approving ADR/research recorded a
  completed governance screen (self-host / air-gap, license, security-scan
  expectation) — the dep was actually reviewed, not merely named.

## Blocks on

- A newly-added dependency with **no** approving research ADR.
- An installed package that **differs** from the ADR-approved one (substitution).
- Extra dependencies added beyond those the ADR approved (unreviewed additions).
- An ADR that names the dep but has **no** completed governance screen.

## Powered by superpowers

Runs at Build/verify via `guardrail-verifier`. A new dependency lacking an ADR is
not a code bug to debug — stop and route back to Shape / research to evaluate and
approve it (or file the ADR) before the checkpoint.

## Notes

- **N/A** for the many slices that add no dependencies (as `migration-safety` is
  N/A without a migration).
- Complements — does not replace — your CI's dependency checks (license boundary,
  dependency-audit, vulnerability scan): those ask "is this dep clean?"; this asks
  "was it reviewed and approved at all?"
