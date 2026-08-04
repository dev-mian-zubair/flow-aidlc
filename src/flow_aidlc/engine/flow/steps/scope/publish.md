# Scope / publish

Create the tracker ticket after deduplication and explicit approval.

This step makes an **outward write** — a ticket is created in the external tracker
and cannot be silently undone. It is therefore a **checkpoint**: do not proceed
without explicit human approval.

## Step 1 — Deduplicate

Before creating anything, search the tracker for existing issues that overlap with
this ticket's intent.

```
Search query: <title keywords> in repo <config.yaml tracker.repo>
```

- If a duplicate exists: **stop**. Link to it, explain the overlap to the user,
  and ask whether to close this draft or proceed with a distinct scope.
- If no duplicate exists: proceed to Step 2.

Deduplication is required by `config.yaml tracker.create.dedupe: true`. It must
not be skipped.

## Step 2 — Show the draft and request approval

Present the full ticket draft (title, description, acceptance criteria, labels)
to the user.

**CHECKPOINT — outward write requires explicit approval.**

```
The following ticket will be created in <config.yaml tracker.repo>.
This action cannot be silently undone.

[Show ticket draft here]

Approve? (yes / no / edit)
```

Do not call the tracker MCP until the user replies with explicit approval ("yes"
or equivalent). A non-answer is not approval.

## Step 3 — Create the ticket

On approval, call the tracker MCP to create the issue:

```
mcp: <config.yaml tracker.mcp>
action: create_issue
repo: <config.yaml tracker.repo>
title: <title>
body: <description + acceptance criteria>
labels: [<type>, <priority>, <area>]
```

## Output

- **Ticket id** — the configured id-scheme identifier (`config.yaml` → `id_scheme`) (the tracker issue number).
- Hand the ticket id to `/flow-start` to begin the Shape phase.

## Notes

- The worklog directory `worklog/<PI-NNN>/` is created by `steps/shared/kickoff.md`
  once the ticket id is known.
- If creation fails (network error, permissions), report the error and retry once
  before escalating to the user.
