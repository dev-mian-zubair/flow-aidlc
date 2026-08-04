# Scope / publish

Create the tracker ticket after deduplication and explicit approval.

This step makes an **outward write** — a ticket is created in the external tracker
and cannot be silently undone. It is therefore a **checkpoint**: do not proceed
without explicit human approval.

## Step 1 — Deduplicate

Before creating anything, search the tracker for existing issues that overlap with
this ticket's intent.

```
Search query: <title keywords> in the tracker repo from config.yaml (tracker.repo)
```

- If a duplicate exists: **stop**. Link to it, explain the overlap to the user,
  and ask whether to close this draft or proceed with a distinct scope.
- If no duplicate exists: proceed to Step 2.

For an **epic**, dedup the parent by intent; a quick check on obviously-named
children is enough — children are stubs and are expected to be new.

Draw dedup search terms from the subsystem's real vocabulary in the Knowledge Map
(`steps/shared/knowledge-map.md`) — the map's naming finds overlaps that the raw
title keywords miss.

Deduplication is required by `config.yaml tracker.create.dedupe: true`. It must
not be skipped.

## Step 2 — Show the draft and request approval

Present the full ticket draft to the user. For an **epic**, present the whole
tree at once — the Epic parent plus every child stub (title + type + size) — and
state that **N+1 issues** will be created and linked as sub-issues; a single
approval covers the batch.

**CHECKPOINT — outward write requires explicit approval.**

```
The following ticket will be created in the tracker repo from config.yaml (tracker.repo).
This action cannot be silently undone.

[Show ticket draft here]

Approve? (yes / no / edit)
```

Do not call the tracker MCP until the user replies with explicit approval ("yes"
or equivalent). A non-answer is not approval.

## Step 3 — Create the ticket(s)

On approval, call the tracker MCP (`config.yaml tracker.mcp`). The method names
below are the current issue toolset — if the connected server predates the
consolidated tools, `issue_write(create)` maps to the older `create_issue`.

**Single ticket (bug / task / feat):**

```
mcp:        <config.yaml tracker.mcp>
tool:       issue_write
method:     create
repo:       <config.yaml tracker.repo>
title:      <title>
body:       <filled ISSUE BODY block>
labels:     [type:<type>, priority:<P0-P3>, area:<area>]
type:       <Bug|Feature|Task>     # only if the tracker has issue types — see fallback
```

**Issue-type fallback:** if the tracker has no matching issue type (or issue types
are disabled), omit the `type:` field — the `type:<...>` **label** already carries
the classification.

**Epic (parent + child stubs):**

1. Create the **Epic parent** with `issue_write(create)` (`type: Epic`, or label
   fallback). Capture its issue number `#E`.
2. For each child stub: `issue_write(create)` with the child's body + labels/type.
   Capture each child number `#C`.
3. Link every child under the parent via the tracker's sub-issue mechanism
   (parent: `#E`, child: `#C`). The tracker then renders the child checklist +
   progress rollup on the Epic automatically.

**Board fields (Priority / Effort / board Status):** not set by `issue_write`.
They require a separate board write after adding the issue to the project board.
For now set these **manually** in the sidebar (or defer to a follow-up) and note
it in the approval summary — do not block creation on them.

## Output

- **Ticket id(s)** — the assigned identifier(s) per the configured id-scheme
  (`config.yaml` → `id_scheme`; the tracker issue number(s)). An epic returns the
  parent id plus each linked child id.
- Hand a single ticket (or a chosen epic child) to `/flow-start` to begin Shape.
  The Epic parent itself is a tracking umbrella — Shape runs per child.

## Notes

- The worklog directory `worklog/<PI-NNN>/` is created by `steps/shared/kickoff.md`
  once the ticket id is known.
- If creation fails (network error, permissions), report the error and retry once
  before escalating to the user.
