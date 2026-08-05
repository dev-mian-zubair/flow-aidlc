# Enable the dependency-provenance guardrail for this task?

The DEP guardrail enforces dependency provenance as a blocking check at Build/verify: every external dependency newly added in the diff must trace to an approved research ADR (from Shape / research) with a completed governance screen — no unreviewed, substituted, or extra dependencies. It complements your CI's license / audit / vulnerability scans, which ask "is this dep clean?" — this asks "was it reviewed and approved at all?"

A) Yes — enforce DEP rules as blocking checks at Build/verify (recommended for any change that adds a third-party dependency, especially in a governed / air-gapped / license-sensitive project)
B) No — skip (fine for a task that adds no new dependencies, or a throwaway prototype)

[Answer]:
