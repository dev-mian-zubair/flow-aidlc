# Test Coverage

**ID prefix:** TEST · **Enforcement:** opt-in (blocking when enabled)

## Rule

New business logic ships with tests; coverage does not regress below the project's floor. Tests are authored under `superpowers:test-driven-development` at Build/generate and assert behavior, not just execution.

## Verification

- **TEST-01** New logic has unit tests: every new function or class carrying business logic has at least one corresponding test in the project's test suite; the test exercises the primary success path and at least one error/edge path.
- **TEST-02** Coverage floor stays green: your CI's coverage step (and any docstring/interrogation check), if configured, does not regress — coverage does not drop below the configured floor; otherwise confirm at review that new logic is exercised by tests.
- **TEST-03** Assertions present: no new test function is assertion-free; every test contains at least one assertion that validates an observable outcome, not merely that the code executed without raising.

## Blocks on

- New business logic with no corresponding test in the suite.
- A coverage regression below the project's configured floor.
- a test that asserts nothing (TEST-03)

## Powered by superpowers

Runs at Build/verify via the `guardrail-verifier`. Tests are authored under `superpowers:test-driven-development` at the Build/generate stage. A failing or flaky test is diagnosed with `superpowers:systematic-debugging` before the checkpoint is cleared.
