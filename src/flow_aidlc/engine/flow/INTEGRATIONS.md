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
`GITHUB_TOKEN`. The server is a **local, headless** stdio process, so it can't run an
interactive login itself — it reads an already-minted token from the environment.

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

Flow defaults to GitHub Issues. To swap to Jira or Linear:

1. Edit `.flow/config.yaml`:
   ```yaml
   tracker:
     platform: linear        # github | jira | linear
     mcp: linear             # must match a key in .mcp.json
   ```
2. Add the corresponding MCP server entry to `.mcp.json` (e.g. `@linear/mcp`) with its env vars,
   and implement its mapping in the tracker adapter `.flow/steps/shared/tracker.md`
   (the `config-consistency` gate check C3 blocks an unimplemented platform).
3. Re-run `flow doctor` to confirm the new server's command resolves and its env var is set.
