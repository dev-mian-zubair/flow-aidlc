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

**Implemented:** `github`, `jira`.  **Stubs:** `linear`.

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

### jira

Tool names are the `mcp-atlassian` (sooperset) Jira toolset. **`config.tracker.repo`
holds the Jira project key** (the `<project-key>` in a `<project-key>-<number>`
issue key), not `owner/repo`; the site base URL is the `JIRA_URL` env var (see
`INTEGRATIONS.md`). Because Jira keys are already `<project-key>-<number>`, set
`config.tracker.id_scheme` to `<project-key>-{n}` (i.e. `flow init --tracker jira
--repo <project-key> --id-prefix <project-key>`, using your real key).

| Operation | jira tool call |
|---|---|
| `DEDUP_SEARCH` | `jira_search` with a JQL query scoped to `project = <config.tracker.repo>` (e.g. `project = <project-key> AND text ~ "<terms>"`) |
| `CREATE_TICKET` | `jira_create_issue(project_key: <config.tracker.repo>, summary: title, description: body, issue_type, labels)` |
| `VERIFY_EXISTS` / `GET_TICKET` | `jira_get_issue(issue_key)` |
| `SET_TYPE` | set `issue_type` at create; change later via `jira_update_issue(fields: {issuetype})`. Jira issue types (Bug/Story/Task/Epic) are native — no label fallback needed |
| `ADD_SUB_ISSUE` | **team-managed:** `jira_update_issue(child, fields: {parent: {key: <parent>}})`; **company-managed classic epics:** `jira_link_to_epic(issue_key: <child>, epic_key: <parent>)`. (`jira_create_issue_link` is for *relates/blocks* links, not parent — do not use it for epic children.) |
| `SET_FIELDS` | `jira_update_issue` — priority → `fields.priority`; effort → the story-points custom field (`customfield_XXXXX`); milestone → `fields.fixVersions`; status is a **transition**, not a field — use `CLOSE`/`jira_transition_issue` |
| `COMMENT` | `jira_add_comment(issue_key, comment)` |
| `CLOSE` | `jira_transition_issue(issue_key, transition: "Done"|"Closed")` — Jira advances state via **workflow transitions**, not a boolean; the target transition name depends on the project's workflow |
| `OPEN_PR` | **Jira does not host code.** Open the PR on the VCS (the `github` mapping's `pull_request_write`), and put the Jira key (e.g. `<project-key>-123`) in the PR title/body so Jira's development panel / Smart Commits link it back. Ship terminates at the open PR; it does not transition the Jira ticket. |

**Preconditions (jira):** the `jira` MCP (`mcp-atlassian`) is connected + authed —
Cloud: `JIRA_URL` + `JIRA_USERNAME` + `JIRA_API_TOKEN`; Server/DC: `JIRA_URL` +
`JIRA_PERSONAL_TOKEN`. The story-points/effort custom-field id is instance-specific;
resolve it once and record it in `knowledge/map/` if `SET_FIELDS` sets effort.

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
