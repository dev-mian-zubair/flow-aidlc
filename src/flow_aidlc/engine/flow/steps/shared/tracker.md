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

**Implemented:** `github`, `jira`, `linear`, `azure-devops`, `shortcut`, `asana`, `clickup`.

> The four sections below (`azure-devops`, `shortcut`, `asana`, `clickup`) map to
> each platform's MCP toolset; tool names track the referenced server and may
> differ across versions — confirm against your installed server. Set
> `config.tracker.mcp` to the server's key in `.mcp.json` and `config.tracker.repo`
> to the platform's container id per each section.

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
resolve it once and record it in `docs/flow/knowledge/map/` if `SET_FIELDS` sets effort.

### linear

Tool names are the Linear MCP toolset (Linear's API operations). **`config.tracker.repo`
holds the Linear team key** (the `<team-key>` in a `<team-key>-<number>` issue id),
not `owner/repo`; auth is the `LINEAR_API_KEY` env var (see `INTEGRATIONS.md`). Because
Linear ids are already `<team-key>-<number>`, set `config.tracker.id_scheme` to
`<team-key>-{n}` (i.e. `flow init --tracker linear --repo <team-key> --id-prefix
<team-key>`, using your real key).

| Operation | linear tool call |
|---|---|
| `DEDUP_SEARCH` | `list_issues` filtered by team (`config.tracker.repo`) + a text query over title/description |
| `CREATE_TICKET` | `create_issue(team: <config.tracker.repo>, title, description, labelIds)` — Linear requires a **team**, not a project |
| `VERIFY_EXISTS` / `GET_TICKET` | `get_issue(id)` |
| `SET_TYPE` | Linear has **no native issue type** — apply a `type:<bug\|feat\|task\|epic>` **label** (like GitHub's label fallback). There is no Epic issue type; an epic is a parent issue (see `ADD_SUB_ISSUE`) or a Linear **Project** |
| `ADD_SUB_ISSUE` | `update_issue(child, parentId: <parent>)` — Linear sub-issues are the `parent` relation. (For a Project-style epic, set the children's `projectId` instead.) |
| `SET_FIELDS` | `update_issue` — priority → `priority` (0–4); effort → `estimate` (points); milestone → `cycleId` or `projectId`; status is a **workflow state**, not a field — use `CLOSE`/set `stateId` |
| `COMMENT` | `create_comment(issueId, body)` |
| `CLOSE` | `update_issue(id, stateId: <a Done/Canceled workflow state>)` — Linear advances state via **workflow states**, not a boolean; the target state id is team-specific (resolve via `list_issue_statuses`) |
| `OPEN_PR` | **Linear does not host code.** Open the PR on the VCS (the `github` mapping's `pull_request_write`), and put the Linear id (e.g. `<team-key>-123`) in the branch name / PR title so Linear's GitHub integration auto-links and can auto-close it. Ship terminates at the open PR; it does not move the Linear issue. |

**Preconditions (linear):** the `linear` MCP is connected + authed via `LINEAR_API_KEY`
(a personal API key from Linear → Settings → Security & access → API). Workflow-state
and label ids are workspace-specific; resolve them once (`list_issue_statuses`,
`list_issue_labels`) and record them in `docs/flow/knowledge/map/` if `SET_TYPE`/`CLOSE` need them.

### azure-devops

Tool names are the `microsoft/azure-devops-mcp` toolset (work-item-tracking `wit_*`
and repo `repo_*` families). **`config.tracker.repo` holds `<org>/<project>`**; work
items are identified by their numeric id. Azure DevOps has **native work-item types**
(Bug/Task/User Story/Epic/Feature) and hosts code in **Azure Repos**, so `OPEN_PR` is
native when you use Azure Repos (else open on your VCS).

| Operation | azure-devops tool call |
|---|---|
| `DEDUP_SEARCH` | `search_workitem` (WIQL/text) scoped to `<project>` |
| `CREATE_TICKET` | `wit_create_work_item(project, type, title, description, fields)` |
| `VERIFY_EXISTS` / `GET_TICKET` | `wit_get_work_item(id)` |
| `SET_TYPE` | set the work-item **type** at create; native types map bug/feat/task/epic → Bug/User Story (or Feature)/Task/Epic |
| `ADD_SUB_ISSUE` | `wit_update_work_item` adding a `System.LinkTypes.Hierarchy-Reverse` parent link (parent → child hierarchy) |
| `SET_FIELDS` | `wit_update_work_item` — priority → `Microsoft.VSTS.Common.Priority`; effort → `…Scheduling.StoryPoints`; milestone → `System.IterationPath`; area → `System.AreaPath` |
| `COMMENT` | `wit_add_work_item_comment(id, text)` |
| `CLOSE` | `wit_update_work_item(id, System.State: "Closed"/"Done")` — state names depend on the process (Agile/Scrum/Basic) |
| `OPEN_PR` | **Azure Repos:** `repo_create_pull_request(...)`. **Code on another VCS:** open there (the `github` mapping) with the work-item id (`#123`) in the PR to auto-link. |

**Preconditions (azure-devops):** the `azure-devops` MCP authed via your Azure login
(PAT/Entra). The state model and field reference names are process-specific; resolve
once and record in `docs/flow/knowledge/map/` if `SET_FIELDS`/`CLOSE` need them.

### shortcut

Tool names are the `useshortcut/mcp-server-shortcut` toolset. Shortcut is
workspace-scoped — **`config.tracker.repo` is unused** (leave empty) and the id is the
numeric **story id**; set `config.tracker.id_scheme` to `sc-{n}`. Stories have a native
**story type** (feature/bug/chore) and epics are first-class.

| Operation | shortcut tool call |
|---|---|
| `DEDUP_SEARCH` | `search-stories(query)` (Shortcut search syntax) |
| `CREATE_TICKET` | `create-story(name, description, story_type, labels, team/group)` |
| `VERIFY_EXISTS` / `GET_TICKET` | `get-story(id)` |
| `SET_TYPE` | set `story_type` at create — feature/bug/chore; an **epic** is created with `create-epic` rather than a story type |
| `ADD_SUB_ISSUE` | set the child story's `epic_id` to the parent epic (epic → stories); story-to-story is a relationship, not parent/child |
| `SET_FIELDS` | `update-story` — priority/estimate/state via workflow-state id, iteration, labels |
| `COMMENT` | `create-story-comment(story_id, text)` |
| `CLOSE` | `update-story(id, workflow_state_id: <a Done state>)` — states are workflow-specific |
| `OPEN_PR` | **Shortcut does not host code.** Open the PR on the VCS with the story id (e.g. `sc-123`) in the branch/PR title so Shortcut's VCS integration links and can auto-complete it. |

**Preconditions (shortcut):** the `shortcut` MCP authed via `SHORTCUT_API_TOKEN`.
Workflow-state and epic ids are workspace-specific; resolve once and record in
`docs/flow/knowledge/map/`.

### asana

Tool names are the `roychri/mcp-server-asana` toolset. **`config.tracker.repo` holds the
Asana project gid** and the id is the numeric **task gid** (set `id_scheme` to a plain
`{n}` or your own prefix). Asana has **no native issue type** — model type with a
`type:*` **tag** or a custom field (label fallback, like github/linear); epics are a
**parent task + subtasks** (or a project/section).

| Operation | asana tool call |
|---|---|
| `DEDUP_SEARCH` | `asana_search_tasks(project/workspace, text)` |
| `CREATE_TICKET` | `asana_create_task(project=<config.tracker.repo>, name, notes, tags)` |
| `VERIFY_EXISTS` / `GET_TICKET` | `asana_get_task(task_gid)` |
| `SET_TYPE` | apply a `type:<bug\|feat\|task\|epic>` **tag** (no native type) |
| `ADD_SUB_ISSUE` | `asana_create_subtask(parent=<parent gid>)`, or `asana_update_task` setting `parent` |
| `SET_FIELDS` | `asana_update_task` — priority/effort via **custom fields**; milestone via section/project; due date |
| `COMMENT` | `asana_create_task_comment(task_gid, text)` |
| `CLOSE` | `asana_update_task(task_gid, completed: true)` |
| `OPEN_PR` | **Asana does not host code.** Open the PR on the VCS; reference the task URL/gid in the PR (Asana's GitHub integration links it). |

**Preconditions (asana):** the `asana` MCP authed via `ASANA_ACCESS_TOKEN` (a personal
access token). Custom-field gids are workspace-specific; resolve once and record in
`docs/flow/knowledge/map/` if `SET_FIELDS` sets priority/effort.

### clickup

Tool names are the ClickUp MCP toolset (community `clickup-mcp`). **`config.tracker.repo`
holds the ClickUp list id** and the id is the **task id** (ClickUp task ids are opaque,
e.g. `86abc`; set `id_scheme` accordingly). ClickUp supports **custom task types** and
subtasks via `parent`.

| Operation | clickup tool call |
|---|---|
| `DEDUP_SEARCH` | `search_tasks` / `get_tasks(list_id=<config.tracker.repo>, query)` |
| `CREATE_TICKET` | `create_task(list_id=<config.tracker.repo>, name, description, tags, custom_item_id?)` |
| `VERIFY_EXISTS` / `GET_TICKET` | `get_task(task_id)` |
| `SET_TYPE` | ClickUp **custom task types** via `custom_item_id`; else a `type:*` tag fallback |
| `ADD_SUB_ISSUE` | `create_task(..., parent=<parent task id>)` (subtasks), or `update_task(parent=…)` |
| `SET_FIELDS` | `update_task` — priority (1–4), points/time-estimate, status, due date; extra fields via **custom fields** |
| `COMMENT` | `create_task_comment(task_id, comment_text)` |
| `CLOSE` | `update_task(task_id, status: "closed"/"done")` — statuses are list/space-specific |
| `OPEN_PR` | **ClickUp does not host code.** Open the PR on the VCS with the task id in the branch/PR; ClickUp's GitHub integration links it. |

**Preconditions (clickup):** the `clickup` MCP authed via `CLICKUP_API_TOKEN` (personal
token; a Team/workspace id may also be required). Status and custom-field ids are
space-specific; resolve once and record in `docs/flow/knowledge/map/`.

## Rule

- Steps and agents invoke operations by **universal name** and cite this file —
  never a platform tool directly. That keeps the whole methodology tracker-neutral.
- The adapter reads `config.tracker.platform` and dispatches. An unmapped or
  stubbed platform is a **hard stop**, not an improvisation.
- Adding a platform = filling in its section here + removing its NOT IMPLEMENTED
  marker, and granting that platform's MCP tool to the tracker-touching agents
  (`scope-publish`, `shape-intake`, and the Ship/release orchestrator). No caller
  **prose** changes — they already use universal operation names.
