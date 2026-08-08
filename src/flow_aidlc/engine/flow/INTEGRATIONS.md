# Flow — Team Setup & MCP Integrations

Everything a new team member needs to run Flow locally: the one-time setup, the
MCP servers declared in `.mcp.json`, the code graph, the env vars, and how to
verify it all in one command.

---

## One-time setup (per clone)

> **Fastest path:** `flow setup` chains the automatable onboarding steps below (the
> code-graph tool, the built graph) and finishes by running `flow doctor`. It is
> idempotent and uses the **detect-and-guide** posture — a missing `uv` or a missing
> graph binary is reported, not fatal, so the run still completes what it can. You then
> only do the things a command can't: set your tracker token (env vars, below), reload
> MCP / restart your client, and enable the Claude Code plugins if they aren't already.
> The manual steps are kept here for reference and for partial re-runs.

```bash
# 1. Install the code-graph tool. The [mcp] extra powers the agent graph MCP
#    (mcp__graphify); the base package alone is enough for the graph build and CI.
uv tool install "graphifyy[mcp]==0.9.33" --force

# 2. Build the code graph — run your configured graph.build (config.yaml → graph.build).
#    The graph artifact is committed, so a fresh clone already has it; rebuild to
#    refresh after you change code. `flow refresh` also rebuilds it.
flow refresh

# 3. Set the MCP env vars (see "Env vars" below) in your shell profile — never commit them.

# 4. Verify everything resolves:
flow doctor
```

Then **reload MCP servers in your client** (in Claude Code, restart the session or
reload) so the `.mcp.json` servers — including `graphify` — actually connect. MCP
servers are read at session start, so a running session won't see a newly added one.

---

## MCP servers (`.mcp.json`)

What each declared server does, what it needs, and whether Flow needs it:

| Server | Role in Flow | Required env var(s) | Core / Optional |
|---|---|---|---|
| tracker (`github` by default) | Issues/PR read-write; Scope's tracker write path | the tracker's token (e.g. `GITHUB_TOKEN` with `repo` scope) | **Core** |
| `graphify` | Code-graph MCP — agents query code *structure* (`WHO_CALLS`/`NEIGHBORS`/`HUBS`) via `mcp__graphify` (Shape/map-existing, curator, scope/clarify, branch-hardening) | _(none — local, offline)_ | **Core** for graph-backed Shape — degrades to `Explore`/grep if absent |
| `context7` | Up-to-date library docs injected at Build — no auth | _(none — public service)_ | **Core** |

---

## Code graph (Graphify)

The code graph is Flow's source of truth for code *structure* (callers, dependents,
contracts); the curated `knowledge/map/` docs hold only the invariants a graph can't
know. Flow reaches the graph only through the graph adapter — the backend is swappable
(Graphify by default). See `steps/shared/graph.md`.

- **Install** — `uv tool install "graphifyy[mcp]==0.9.33" --force`. The **base** package
  (`graphifyy==0.9.33`) is CLI-only and enough for the graph build and CI; the **`[mcp]`
  extra** is required for the `graphify-mcp` server that agents query. Without `[mcp]`,
  `graphify-mcp` errors and the graph consumers fall back to `Explore`/grep — nothing
  breaks, callers are just non-deterministic.
- **Build / refresh** — run your configured `graph.build` (canonical, deterministic,
  offline); `flow refresh` wraps it. The graph artifact is committed, so you only rebuild
  after changing product code.
- **Verify** — `flow doctor` (checks the CLI, the built graph, and the MCP wiring). Quick
  sanity queries: `graphify god-nodes`, or `graphify affected "<symbol>"`.
- **Air-gap** — the build is fully offline (local AST, no API key); vendor the wheel for
  an air-gapped host if needed.

---

## Claude Code plugins

Flow relies on two Claude Code plugins from the official `claude-plugins-official`
marketplace:

| Plugin | Role in Flow |
|---|---|
| `superpowers` | The skill engine behind the playbook (brainstorming, TDD, verification, plan execution) — the governed path is "powered by superpowers". |
| `pr-review-toolkit` | The reviewer agents used at Ship / branch-hardening. |

They are declared at **project scope** in `.claude/settings.json` (`enabledPlugins`),
so a teammate who opens **and trusts** this repo in Claude Code gets them automatically.
As a fallback, install them user-globally via the `claude` CLI, then **restart Claude
Code** so the plugins load (like MCP servers, plugins are read at session start).

---

## Env vars

The only required var is your **tracker token** (for the tracker MCP server —
`graphify` and `context7` need none). With the default GitHub tracker that is
`GITHUB_TOKEN`; with the Jira tracker it is `JIRA_URL` + `JIRA_USERNAME` +
`JIRA_API_TOKEN` (Cloud) or `JIRA_URL` + `JIRA_PERSONAL_TOKEN` (Server/DC); with the
Linear tracker it is `LINEAR_API_KEY` — see "Switching the issue tracker". The server
is a **local, headless** stdio process, so
it can't run an interactive login itself — it reads an already-minted token from the
environment.

**Recommended — source it from the `gh` CLI's OAuth login** (no hand-minted PAT):

```bash
gh auth login                        # interactive GitHub OAuth (browser) — done once
gh auth refresh -s repo              # ensure 'repo' scope for issues/PRs, if missing
# then in your shell profile (~/.zshrc / ~/.bashrc):
export GITHUB_TOKEN=$(gh auth token) # re-reads gh's stored token each shell — no secret in the dotfile
```

**Fallback — a manual Personal Access Token** (if you don't use `gh`):

```bash
export GITHUB_TOKEN=ghp_...          # 'repo' scope (or 'public_repo' for public repos) — never commit it
```

---

## Credentials & secrets

Flow reads MCP credentials from the environment via `${VAR}` references in
`.mcp.json` (committed — it holds no secrets). You supply the values one of
three ways, best DX first:

1. **Secrets manager (recommended, zero plaintext)** — `flow secrets use infisical`
   rewrites every secret-bearing MCP server to `infisical run -- …`, so the
   token is injected at launch and never touches the repo, `.env`, or your
   shell. One-time: `infisical login` (stores a token in your OS keyring) +
   `infisical init` (links the project). `flow secrets off` reverts; `flow
   secrets status` verifies resolution. (`op`/`doppler` aren't wired
   first-class yet — `flow secrets use <name>` prints the manual `<tool> run --
   …` wrapper to apply by hand, and exits non-zero.)
2. **Provider CLI credential store** — e.g. `export GITHUB_TOKEN=$(gh auth token)`
   keeps the secret in `gh`'s store, not a file.
3. **`.env` file (fallback)** — copy the generated `.env.example` to `.env`
   (gitignored), fill it in, and load it (`direnv`, or `set -a; source .env;
   set +a`) before launching Claude Code. `flow doctor` warns when a required
   var is unset in the environment but present in an unsourced `.env`.

`flow doctor` reports a `secrets` line covering every secret-bearing server;
`flow secrets status` adds a live resolve probe.

---

## Verifying your setup

```bash
flow doctor
```

It is read-only. It reports, per section:

- **Config files** — `.flow/playbook.md`, `.flow/config.yaml`, `.claude/settings.json`, `.mcp.json` present.
- **Env vars** — every `${VAR}` placeholder in `.mcp.json` is set.
- **MCP commands** — each server's command resolves on `PATH` (`graphify-mcp`, `npx`).
- **Hooks** — `.claude/hooks/*.sh` are executable.
- **Code graph** — the graph CLI present and the graph artifact built.

Each ✗ line names the fix (an install command or a config value).

---

## Switching the issue tracker

Flow defaults to GitHub Issues. `github`, `jira`, and `linear` are all implemented in
the tracker adapter (`.flow/steps/shared/tracker.md`) — switching is a config +
`.mcp.json` change, no adapter work.

### To Jira (implemented — `mcp-atlassian`)

Jira is mapped to the `mcp-atlassian` (sooperset) toolset. Jira does not use
`owner/repo` — `config.tracker.repo` holds the **project key** and the site URL is an
env var. Because Jira keys are already `<project-key>-<number>`, the id-scheme prefix
is the project key.

1. Scaffold (or edit `.flow/config.yaml`) for Jira — substitute your real key for
   `<project-key>`:
   ```bash
   flow init --tracker jira --repo <project-key> --id-prefix <project-key>
   ```
   ```yaml
   tracker:
     platform: jira
     mcp: jira                       # must match the key in .mcp.json
     repo: <project-key>             # the Jira project key (not owner/repo)
     id_scheme: <project-key>-{n}    # Jira keys are already <project-key>-<n>
   ```
2. Add the `jira` server to `.mcp.json` (headless stdio, matches Flow's model):
   ```json
   "jira": {
     "command": "uvx",
     "args": ["mcp-atlassian"],
     "env": {
       "JIRA_URL": "${JIRA_URL}",
       "JIRA_USERNAME": "${JIRA_USERNAME}",
       "JIRA_API_TOKEN": "${JIRA_API_TOKEN}"
     }
   }
   ```
   Cloud auth: `JIRA_URL` (e.g. `https://your-site.atlassian.net`), `JIRA_USERNAME`
   (your email), `JIRA_API_TOKEN` (from id.atlassian.com). Server/DC: use
   `JIRA_PERSONAL_TOKEN` instead of username + api-token.
3. `flow doctor` to confirm the `jira` server resolves and its env vars are set;
   `flow check` — C3 passes because the adapter implements `jira`.

> **Code still lives on your VCS.** Jira tracks issues; it does not host PRs. With
> `platform: jira` the Ship phase still opens the PR on your VCS (the `github`
> mapping's `pull_request_write`) with the Jira key in the PR title/body — keep the
> `github` MCP server declared for the PR write path.

### To Linear (implemented — Linear MCP)

Linear is mapped to the Linear MCP toolset. Linear does not use `owner/repo` —
`config.tracker.repo` holds the **team key** (issues are `<team-key>-<number>`), and
auth is a personal API key. Because Linear ids are already `<team-key>-<number>`, the
id-scheme prefix is the team key.

1. Scaffold (or edit `.flow/config.yaml`) for Linear — substitute your real key for
   `<team-key>`:
   ```bash
   flow init --tracker linear --repo <team-key> --id-prefix <team-key>
   ```
   ```yaml
   tracker:
     platform: linear
     mcp: linear                  # must match the key in .mcp.json
     repo: <team-key>             # the Linear team key (not owner/repo)
     id_scheme: <team-key>-{n}    # Linear ids are already <team-key>-<n>
   ```
2. Add the `linear` server to `.mcp.json` (headless stdio, matches Flow's model):
   ```json
   "linear": {
     "command": "npx",
     "args": ["-y", "linear-mcp-server"],
     "env": { "LINEAR_API_KEY": "${LINEAR_API_KEY}" }
   }
   ```
   Auth: `LINEAR_API_KEY` — a personal API key from Linear → Settings → Security &
   access → API. (Prefer the stdio server above; Linear also offers a remote OAuth MCP
   at `https://mcp.linear.app/sse` if you'd rather not mint a key.)
3. `flow doctor` to confirm the `linear` server resolves and its env var is set;
   `flow check` — C3 passes because the adapter implements `linear`.

> **Code still lives on your VCS.** Linear tracks issues; it does not host PRs. With
> `platform: linear` the Ship phase still opens the PR on your VCS (the `github`
> mapping's `pull_request_write`) with the Linear id in the branch/PR title — keep the
> `github` MCP server declared for the PR write path (Linear's GitHub integration then
> auto-links and can auto-close the issue on merge).
