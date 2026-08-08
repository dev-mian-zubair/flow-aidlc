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
  infisical` rewrites the tracker MCP server to inject its token at launch, with
  **no secret in the repo, no `.env`, no shell export**.
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
| `.env` loading | Guided only + doctor "present but not loaded" safety net |
| doctor probe depth | Shallow (offline) in `doctor`; deep (network) only in `flow secrets status` |
| `.env.example` source | Generated in `flow init` from a per-tracker required-var map |

## 5. Command surface & architecture

New subcommand `flow secrets`, a thin dispatcher over a **provider registry**:

```
flow secrets use <provider> [--env <name>] [--dry-run]   # wrap the tracker MCP server
flow secrets off [--dry-run]                             # unwrap → restore plain form
flow secrets status                                      # detailed, verifying report
```

- Providers are data: `infisical` implemented; `op` / `doppler` recognized (print
  the manual `<tool> run --` wrapper + "first-class wiring coming").
- Only the **tracker server** is ever touched — resolved via
  `config.yaml → tracker.mcp` (the server key in `.mcp.json`), never hardcoded, so
  it works for github/jira/linear.

## 6. `.mcp.json` wrapping mechanics

`use infisical` rewrites only the tracker server's `command`/`args`:

```jsonc
// before
"github": { "command": "npx", "args": ["-y","@modelcontextprotocol/server-github"],
            "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" } }
// after — env block dropped; Infisical injects the token into the child process
"github": { "command": "infisical", "args": ["run","--","npx","-y","@modelcontextprotocol/server-github"] }
```

With `--env prod`, args become `["run","--env","prod","--",...]`.

- **Idempotent** — an already-wrapped server (`command == "infisical"` with a
  `run ... --` prefix) is detected; no double-wrap.
- **Reversible** — `off` strips everything up to and including the `--` sentinel,
  reconstructing the original `command`/`args` generically, and restores the
  `${VAR}` env block from the per-tracker var map (see §8).
- **Round-trip assumption** — wrap/unwrap targets the **standard engine-shaped**
  tracker server (a single token-var `env` block, as `flow init` produces). If a
  user hand-added extra `env` keys, `off` restores only the standard block; this
  is documented, and `--dry-run` shows the exact result before writing.
- **Cross-platform safe** — `command: "infisical"` (not `sh -c`), so it works
  natively on Windows (a key advantage over `.env` auto-wiring).
- **`--dry-run`** prints the diff and writes nothing. `.mcp.json` is committed, so
  a wrap is a reviewable change.
- **Provider switch** — `use X` when wrapped by `Y` unwraps then rewraps
  (idempotent to the target).

## 7. Preconditions & the mode-aware credential check

`use infisical` uses Flow's **detect + guide + keep going** posture: checks
`infisical` on PATH, an active login (keyring token), and `.infisical.json`
(from `infisical init`). Missing pieces are printed guidance, not hard failures.

A **shared credential check** (reported by `flow doctor` under a `secrets` line,
and in full by `flow secrets status`):

- **Wrapped mode** (tracker server `command` is a known secrets tool):
  - `doctor` (shallow, offline, fast): tool on PATH? `.infisical.json` present?
  - `flow secrets status` (deep): additionally run a resolve probe
    (e.g. `infisical run -- printenv <VAR>` / `infisical secrets --silent`) to
    confirm auth + the token actually resolve over the network.
- **Plain `${VAR}` mode**: each placeholder set in the environment? If a var is
  unset **but present in `.env`** → "`.env` present but not loaded — source it or
  use direnv."
- **WARN, never FAIL** — `doctor`/CI stay green (CI often lacks any of this).

This replaces the currently-false `INTEGRATIONS.md` claim with a real check.

## 8. `.env` fallback scaffolding (in `flow init`)

For users who don't adopt a secrets manager, `flow init`:

- writes a committed **`.env.example`** listing required vars for the chosen
  tracker, from a per-tracker var map:
  - `github` → `GITHUB_TOKEN`
  - `jira` → `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`
  - `linear` → `LINEAR_API_KEY`
- adds **`.env`** to `.gitignore` (alongside `worklog/.active`, `.superpowers/`).

It does **not** create a real `.env` (no empty secret file) and does not load it.
The same per-tracker var map is the single source of truth used by `secrets off`
(to restore the `${VAR}` env block) and by the doctor `${VAR}`-mode check.

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

- **`tests/test_secrets.py`** (new): wrap idempotent; `off` round-trips to the
  exact original; wrap targets the `config.tracker.mcp` server (not hardcoded);
  `--dry-run` writes nothing; unknown provider errors cleanly; provider switch
  unwrap-then-rewrap. **Infisical CLI presence mocked via PATH** — tests never
  require it installed; the deep probe is injected/skipped.
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

1. `flow secrets use infisical` (in a repo with a wrappable tracker server)
   rewrites only the tracker server to the `infisical run --` form, idempotently;
   `flow secrets off` restores the original exactly. `--dry-run` writes nothing.
2. `flow doctor` reports a `secrets` line: PASS/WARN per mode, `any_fail`
   unaffected; `flow secrets status` additionally reports the deep probe result.
3. `flow init --tracker <t>` produces a committed `.env.example` with `<t>`'s vars
   and a gitignored `.env`.
4. Full suite green; no engine-template drift; github/jira/linear regressions
   pass.
