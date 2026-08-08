# Design — `flow secrets`: credential DX for tracker MCP servers

**Date:** 2026-08-08
**Status:** Approved (brainstorming) — ready for implementation planning
**Topic:** A credential broker that lets Flow wire a secrets manager (Infisical
first) into the tracker MCP server, plus a `.env` fallback and a mode-aware
credential health check.

---

## 1. Problem

Flow's tracker MCP servers (`github` / `jira` / `linear`) need credentials. Today
`.mcp.json` declares an env indirection — `"GITHUB_TOKEN": "${GITHUB_TOKEN}"` —
and Claude Code resolves `${VAR}` from **its own process environment** when it
launches the server. The documented path is `export`-in-shell-profile (or
`export GITHUB_TOKEN=$(gh auth token)`).

Two gaps:

1. **DX / security.** `export` in a shell profile is global (pollutes every
   project) and, if a literal token is used, puts a secret in a dotfile. Teams
   want a per-project, zero-plaintext, ideally self-hostable option.
2. **No verification.** `INTEGRATIONS.md` claims `flow doctor` checks that every
   `${VAR}` placeholder in `.mcp.json` is set — **it does not**. A missing
   credential is silently undetected until a `/flow-*` run fails mid-stage.

## 2. Goals

- Make a **secrets manager a first-class, wired path** — `flow secrets use
  infisical` rewrites **every secret-bearing MCP server** to inject its
  credentials at launch, with **no secret in the repo, no `.env`, no shell
  export**. Once adopted, **all Flow secrets** (the tracker token *and* any other
  secret an MCP server needs — e.g. the read-only DB URI for the postgres MCP)
  come from the manager, not the environment.
- Add a **mode-aware credential health check** to `flow doctor` (and a deeper
  verifying `flow secrets status`), closing the doc/code gap. WARN, never FAIL.
- Provide a **`.env` fallback** for users who don't adopt a secrets manager:
  scaffold `.env.example` + gitignore `.env`, with a doctor warning when `.env`
  exists but isn't loaded.
- Structure the command as a **provider broker** so `op` / `doppler` can be added
  later as data, without new command surface.

## 3. Non-goals (YAGNI — explicit exclusions)

- Flow does **not** run `infisical login` / `infisical init` (those own
  interactive auth) — it detects and guides.
- Flow does **not** manage Infisical project IDs or environments beyond passing
  an optional `--env`.
- `op` / `doppler` are **not** wired first-class in this slice — recognized names
  that print the manual wrapper pattern.
- Flow does **not** auto-load `.env` (no `sh -c` command wrapping — POSIX-only and
  fragile). `.env` loading stays the user's choice (direnv / manual source),
  backed by the doctor warning.

## 4. Decisions captured during brainstorming

| Decision | Choice |
|---|---|
| Scope | Pragmatic first slice **plus** first-class Infisical wiring |
| Infisical role | First-class **wired** path (not just documented) |
| Wiring mechanism | Dedicated **`flow secrets`** subcommand (extensible broker) |
| Wrap target | **All secret-bearing servers** (any with a `${VAR}` env block), not just the tracker |
| `.env` loading | Guided only + doctor "present but not loaded" safety net |
| doctor probe depth | Shallow (offline) in `doctor`; deep (network) only in `flow secrets status` |
| Secret inventory | Derived by **scanning `.mcp.json` for `${VAR}` references** — the single source of truth for "what are Flow's secrets" |

## 5. Command surface & architecture

New subcommand `flow secrets`, a thin dispatcher over a **provider registry**:

```
flow secrets use <provider> [--env <name>] [--dry-run]   # wrap the tracker MCP server
flow secrets off [--dry-run]                             # unwrap → restore plain form
flow secrets status                                      # detailed, verifying report
```

- Providers are data: `infisical` implemented; `op` / `doppler` recognized (print
  the manual `<tool> run --` wrapper + "first-class wiring coming").
- **Every secret-bearing server** is wrapped — a server "bears secrets" iff its
  `env` block contains one or more `${VAR}` references. Non-secret servers
  (`graphify`, `context7`) have no such block and are left untouched. This covers
  the tracker (github/jira/linear) *and* any other secret server (e.g. postgres
  via `FLOW_DB_READONLY_URI`) uniformly, with no per-platform special-casing.

## 6. `.mcp.json` wrapping mechanics

`use infisical` rewrites **each secret-bearing server**. Per server it stashes the
original config under an ignored `_flowWrapped` key (Claude Code ignores unknown
per-server keys), replaces `command`/`args` with the wrapper, and drops the
top-level `env` block (Infisical injects the values into the child):

```jsonc
// before
"github": { "command": "npx", "args": ["-y","@modelcontextprotocol/server-github"],
            "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" } }
// after
"github": {
  "command": "infisical", "args": ["run","--","npx","-y","@modelcontextprotocol/server-github"],
  "_flowWrapped": { "provider": "infisical",
                    "command": "npx", "args": ["-y","@modelcontextprotocol/server-github"],
                    "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" } }
}
```

With `--env prod`, args become `["run","--env","prod","--",...]`.

- **Lossless round-trip** — `off` restores each server verbatim from
  `_flowWrapped` and deletes the stash. No var map or reconstruction guessing, and
  it round-trips **even hand-customized servers** (extra env keys, custom args).
- **Idempotent** — presence of `_flowWrapped` marks a server as wrapped; re-running
  `use` is a no-op for already-wrapped servers.
- **Env block dropped on wrap (correctness)** — removing the `${VAR}` block means
  the manager's injected value is the *only* source; no stale/empty `${VAR}` can
  shadow it. The original block lives safely in `_flowWrapped` for restore.
- **Cross-platform safe** — `command: "infisical"` (not `sh -c`), so it works
  natively on Windows (a key advantage over `.env` auto-wiring).
- **`--dry-run`** prints the per-server diff and writes nothing. `.mcp.json` is
  committed, so a wrap is a reviewable change.
- **Provider switch** — `use X` when wrapped by `Y` unwraps (from `_flowWrapped`)
  then rewraps, idempotent to the target.

## 7. Preconditions & the mode-aware credential check

`use infisical` uses Flow's **detect + guide + keep going** posture: checks
`infisical` on PATH, an active login (keyring token), and `.infisical.json`
(from `infisical init`). Missing pieces are printed guidance, not hard failures.

A **shared credential check** (reported by `flow doctor` under a `secrets` line,
and in full by `flow secrets status`) evaluates **every secret-bearing server**
and reports the aggregate:

- **Wrapped mode** (server `command` is a known secrets tool):
  - `doctor` (shallow, offline, fast): tool on PATH? `.infisical.json` present?
  - `flow secrets status` (deep): additionally run a resolve probe
    (e.g. `infisical run -- printenv <VAR>` / `infisical secrets --silent`) to
    confirm auth + the values actually resolve over the network.
- **Plain `${VAR}` mode**: each placeholder (across all secret-bearing servers)
  set in the environment? If a var is unset **but present in `.env`** → "`.env`
  present but not loaded — source it or use direnv."
- **Mixed** — some servers wrapped, some plain — is reported per server so a
  half-migrated repo is visible.
- **WARN, never FAIL** — `doctor`/CI stay green (CI often lacks any of this).

This replaces the currently-false `INTEGRATIONS.md` claim with a real check.

## 8. `.env` fallback scaffolding (in `flow init`)

For users who don't adopt a secrets manager, `flow init`:

- writes a committed **`.env.example`** listing **every `${VAR}` referenced in the
  freshly-rendered `.mcp.json`** — the complete Flow secret inventory. For the
  default github tracker that is `GITHUB_TOKEN`; jira adds `JIRA_URL`,
  `JIRA_USERNAME`, `JIRA_API_TOKEN`; linear `LINEAR_API_KEY`; a configured postgres
  MCP adds `FLOW_DB_READONLY_URI`; and any future secret server is covered for free.
- adds **`.env`** to `.gitignore` (alongside `worklog/.active`, `.superpowers/`).

It does **not** create a real `.env` (no empty secret file) and does not load it.
**Scanning `.mcp.json` for `${VAR}` references is the single source of truth** for
the secret inventory — used by `.env.example` generation and by the doctor
`${VAR}`-mode check. (`secrets off` does not need it: it restores from
`_flowWrapped`, see §6.)

## 9. Provider abstraction

```python
@dataclass
class Provider:
    cli: str                                   # e.g. "infisical"
    run: Callable[[list[str], list[str]], list[str]]  # (orig_cmd, env_flags) -> wrapped argv
    preconditions: Callable[[Path], list[str]]        # returns guidance strings
    probe: Callable[[Path], bool] | None              # deep resolve check (status only)

_PROVIDERS = { "infisical": Provider(...) }   # op/doppler added later as entries
```

Adding a provider = one dict entry + docs. No new command surface. This mirrors
the tracker/graph adapter pattern already in the engine.

## 10. Testing

- **`tests/test_secrets.py`** (new): wrap targets **all** secret-bearing servers
  and leaves non-secret ones (graphify/context7) untouched; wrap idempotent;
  `off` round-trips every server to the exact original via `_flowWrapped`
  (including a hand-customized server with extra env/args); `--dry-run` writes
  nothing; unknown provider errors cleanly; provider switch unwrap-then-rewrap.
  **Infisical CLI presence mocked via PATH** — tests never require it installed;
  the deep probe is injected/skipped.
- **`tests/test_doctor.py`** (extend): wrapped-mode, `${VAR}`-mode, and
  `.env`-present-but-not-loaded lines — all assert `any_fail is False`.
- **`tests/test_init.py`** (extend): `.env.example` scaffolded with the right vars
  per tracker; `.env` gitignored.

## 11. Files touched

- **New:** `src/flow_aidlc/commands/secrets.py`, `tests/test_secrets.py`
- **Modified:** `src/flow_aidlc/cli.py` (register `secrets`);
  `src/flow_aidlc/commands/doctor.py` (shared mode-aware credential check);
  `src/flow_aidlc/commands/init.py` (`.env.example` + `.env` gitignore);
  `src/flow_aidlc/engine/flow/INTEGRATIONS.md` (document `flow secrets` + the
  credential ladder with Infisical); `README.md` (one line); tests.
- **No engine template change** — wrapping operates on the instance's `.mcp.json`
  at runtime, not on `mcp.tmpl.json`.

## 12. Acceptance

1. `flow secrets use infisical` rewrites **every secret-bearing server** to the
   `infisical run --` form (stashing originals in `_flowWrapped`), leaving
   non-secret servers untouched, idempotently; `flow secrets off` restores every
   server exactly. `--dry-run` writes nothing.
2. `flow doctor` reports a `secrets` line aggregating all secret-bearing servers:
   PASS/WARN per mode, `any_fail` unaffected; `flow secrets status` additionally
   reports the deep probe result per server.
3. `flow init --tracker <t>` produces a committed `.env.example` containing every
   `${VAR}` in the rendered `.mcp.json` (tracker vars + any others) and a
   gitignored `.env`.
4. Full suite green; no engine-template drift; github/jira/linear regressions
   pass.
