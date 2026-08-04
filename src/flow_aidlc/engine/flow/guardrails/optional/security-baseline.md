# Security Baseline

**ID prefix:** SEC · **Enforcement:** opt-in (blocking when enabled)

## Rule

New code follows secure-by-default patterns and passes your project's security gates. No secrets are introduced into the codebase; static analysis (SAST) is clean at high confidence; outbound HTTP is guarded against SSRF; bare `except:` clauses are absent on auth and integration paths; all input is validated at the trust boundary.

## Verification

- **SEC-01** No secrets in code (review-time rule): the diff introduces no hardcoded secrets, API keys, tokens, or credentials; secrets are read from environment variables or a secret manager, never committed to the repository. Backstop with your CI's secret-scan step (e.g. gitleaks), if configured.
- **SEC-02** SAST clean: your CI's static-analysis step (e.g. bandit, semgrep, CodeQL), if configured, returns no high-confidence findings for the changed files; otherwise this is a review-time check of the diff for the same class of issues.
- **SEC-03** SSRF-safe outbound HTTP: any new code making outbound HTTP calls routes through the project's SSRF-safe HTTP wrapper (if one exists) or otherwise validates the destination; raw fetches to caller-supplied URLs that bypass that guard are absent. Enforce via your CI's SSRF check if configured, else at review.
- **SEC-04** No bare `except:` on auth/integration paths: no new bare `except:` (or over-broad catch that swallows errors) is introduced on authentication or external-integration code. Enforce via your CI's lint step over the security-sensitive files if configured, else at review.
- **SEC-05** Input validated at the boundary: every new endpoint's request body / query params / path params are validated by a typed schema; no handler accepts raw untyped input at its signature.

## Blocks on

- Any new secret literal or credential committed to the codebase.
- A new high-confidence SAST finding in changed files.
- Raw outbound HTTP to a caller-controlled URL that bypasses the SSRF guard.
- A bare `except:` clause introduced on an auth or integration code path.

## Powered by superpowers

Runs at Build/verify via the `guardrail-verifier`. A flagged finding whose root cause is ambiguous is diagnosed with `superpowers:systematic-debugging` before the checkpoint is cleared.
