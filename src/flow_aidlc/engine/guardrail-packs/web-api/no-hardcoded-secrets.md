# No Hardcoded Secrets

**ID prefix:** SECRT · **Enforcement:** blocking when enabled

## Rule

Secrets — API keys, tokens, passwords, connection strings with credentials, private keys — are never committed as literals in source, config, or tests. They are read from the environment (or a secrets manager; see `flow secrets`), and only `${VAR}`-style references or placeholders appear in tracked files.

## Verification

- **SECRT-01** No literal credentials: the diff introduces no hardcoded secret — no inline API key/token/password, no connection string embedding a real credential, no committed private key or `.pem`/`.key` body.
- **SECRT-02** Env/manager indirection: newly-needed secrets are read via an environment variable or a secrets-manager reference; configuration files carry a `${VAR}` reference or a clearly-fake placeholder, not the real value.
- **SECRT-03** Tests use fakes: test fixtures use obviously non-real placeholder values (e.g. `test-token`, `${...}`), never a real credential copied in "just to make it pass".

## Blocks on

- A hardcoded API key, token, password, or credential-bearing connection string in any tracked file.
- A committed private key or certificate private-key body.
- A real secret pasted into a test fixture (SECRT-03).

## Powered by superpowers

Runs at Build/verify via the `guardrail-verifier`. Pairs with `flow secrets` (route MCP/tooling credentials through a manager) and the optional `security-baseline` guardrail.
