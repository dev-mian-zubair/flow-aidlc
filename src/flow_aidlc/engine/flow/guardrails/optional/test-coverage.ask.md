# Enable the test-coverage guardrail for this task?

The TEST guardrail enforces test hygiene as blocking checks at Build/verify: new business logic must have unit tests in the project's test suite, your CI's coverage floor (and any docstring check) must stay green where configured, and every test must contain real assertions — not just execution checks.

A) Yes — enforce TEST rules as blocking checks (recommended for any change that adds or modifies business logic in services, API routes, repos, or domain modules)
B) No — skip (acceptable for pure infrastructure changes, config updates, or doc-only work with no new logic)

[Answer]:
