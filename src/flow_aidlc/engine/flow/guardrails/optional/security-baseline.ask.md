# Enable the security-baseline guardrail for this task?

The SEC guardrail enforces secure-by-default patterns as blocking checks: no secrets in code, static analysis (SAST) clean at high confidence, SSRF-safe outbound HTTP, no bare `except:` on auth/integration paths, and validated inputs at every trust boundary. It backstops with your CI's secret-scan / SAST / SSRF steps where configured, and is a review-time check otherwise.

A) Yes — enforce SEC rules as blocking checks at Build/verify (recommended for anything user-facing, touching auth/integrations, or production-bound)
B) No — skip (acceptable for a throwaway prototype or a purely internal tooling change with no network or auth surface)

[Answer]:
