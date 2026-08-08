# Input Validation at the Boundary

**ID prefix:** VALID · **Enforcement:** blocking when enabled

## Rule

External input (request bodies, query/path params, headers, webhook payloads, queue messages) is validated and typed at the boundary before it reaches business logic. Validation is allow-list (accept known-good shapes) rather than deny-list, and rejected input fails with a client error, never a partial write.

## Verification

- **VALID-01** Boundary validation: every new endpoint/handler parses external input through an explicit schema/validator (types, required fields, ranges, formats) before use; raw request fields are not passed directly into queries, filesystem paths, or shell/command construction.
- **VALID-02** Allow-list shape: validation accepts a known-good structure and rejects unknown/extra fields where they would be security- or integrity-relevant, rather than only blocking a few bad patterns.
- **VALID-03** Reject cleanly: invalid input returns a 4xx-class client error with no side effect performed — no partial write, no external call made on the strength of unvalidated data.

## Blocks on

- A new handler that reads an external field and uses it (query, path, template, command) without validation.
- Validation that mutates state before confirming the whole input is valid (partial write on bad input).
- Unvalidated pass-through of a request field into a data store or interpreter.

## Powered by superpowers

Runs at Build/verify via the `guardrail-verifier`. A suspected injection or unvalidated path is traced with `superpowers:systematic-debugging` before the checkpoint is cleared.
