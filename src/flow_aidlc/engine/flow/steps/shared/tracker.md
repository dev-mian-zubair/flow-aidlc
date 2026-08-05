# Tracker Adapter

The single place that maps Flow's **universal tracker operations** to the tools of
the configured platform. Every step and agent that touches the tracker uses the
universal operation names below and looks the mapping up here — **no step or agent
names a platform-specific tool directly.**

## Select the platform

Read `config.yaml → tracker.platform` (and `tracker.mcp`, `tracker.repo`). Use the
mapping section for that platform. **If the configured platform has no mapping here
— or its section is marked NOT IMPLEMENTED — STOP.** The adapter does not support
it yet; do not improvise platform calls. (The `config-consistency` check enforces
that `tracker.platform` is an implemented platform.)

**Implemented:** `github`.  **Stubs:** `jira`, `linear`.

## Universal operations (the contract callers use)

| Operation | Inputs | Returns | Purpose |
|---|---|---|---|
| `DEDUP_SEARCH` | keywords | matching tickets | find overlapping tickets before creating |
| `CREATE_TICKET` | title, body, labels, type? | ticket id | create a ticket |
| `VERIFY_EXISTS` / `GET_TICKET` | id | exists? + fields | confirm/read a ticket |
| `SET_TYPE` | id, type | — | set the native issue type (Bug/Feature/Task/Epic) |
| `ADD_SUB_ISSUE` | parent id, child id | — | link a child under a parent (epic → children) |
| `SET_FIELDS` | id, {priority, effort, status, milestone} | — | set board / project fields |
| `COMMENT` | id, body | — | post a comment |
| `CLOSE` | id | — | close a ticket |
| `OPEN_PR` | title, body (incl. `Fixes <id>`) | pr url | open a pull/merge request |

Callers cite operations by name, e.g. *"perform `CREATE_TICKET` (see
`steps/shared/tracker.md`)"* — never the underlying tool.

## Platform mappings

### github

Tool names are the current `github-mcp-server` toolset; older servers may split
`issue_write` into `create_issue` / `update_issue`. `owner/repo` = `config.tracker.repo`.

| Operation | github tool call |
|---|---|
| `DEDUP_SEARCH` | `search_issues` (in `tracker.repo`) |
| `CREATE_TICKET` | `issue_write(method: create, title, body, labels, type?)` |
| `VERIFY_EXISTS` / `GET_TICKET` | `search_issues` / issue read by number |
| `SET_TYPE` | `list_issue_types` → `issue_write(type=…)`; fall back to the `type:<…>` **label** if org issue types are disabled |
| `ADD_SUB_ISSUE` | `sub_issue_write(method: add, issue_number: <parent>, sub_issue_id: <child>)` |
| `SET_FIELDS` | Projects v2 — add issue to project, then `projects_write(updated_field: …)`. Not settable via `issue_write`; may be a manual step. |
| `COMMENT` | `add_issue_comment` |
| `CLOSE` | `issue_write(method: update, state: closed)` — or rely on `Fixes #<id>` auto-close |
| `OPEN_PR` | `pull_request_write(method: create, …)` with `Fixes #<id>` in the body |

**Preconditions (github):** the github MCP is connected + authed; native issue
Types require the org to have them enabled (else `SET_TYPE` → label fallback);
`SET_FIELDS` requires your delivery Project v2 to exist.

### jira — NOT IMPLEMENTED

Stub. When adopted, map each universal operation to the Jira MCP/REST equivalent
(`CREATE_TICKET` → create issue; `ADD_SUB_ISSUE` → parent/epic link; `SET_TYPE` →
issue type; `SET_FIELDS` → custom fields; `OPEN_PR` → the linked VCS). Until this
section is filled in, `config.tracker.platform: jira` is refused by
`config-consistency`.

### linear — NOT IMPLEMENTED

Stub. Map to Linear's API (issues, sub-issues via `parent`, projects/labels,
states) when adopted.

## Rule

- Steps and agents invoke operations by **universal name** and cite this file —
  never a platform tool directly. That keeps the whole methodology tracker-neutral.
- The adapter reads `config.tracker.platform` and dispatches. An unmapped or
  stubbed platform is a **hard stop**, not an improvisation.
- Adding a platform = filling in its section here + removing its NOT IMPLEMENTED
  marker, and granting that platform's MCP tool to the tracker-touching agents
  (`scope-publish`, `shape-intake`, and the Ship/release orchestrator). No caller
  **prose** changes — they already use universal operation names.
