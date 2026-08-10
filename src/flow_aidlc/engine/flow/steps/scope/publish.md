# Scope / publish

Create the tracker ticket after deduplication and explicit approval.

This step makes an **outward write** — a ticket is created in the external tracker
and cannot be silently undone. It is therefore a **checkpoint**: do not proceed
without explicit human approval.

## Step 1 — Deduplicate

Before creating anything, perform `DEDUP_SEARCH` (see `steps/shared/tracker.md`)
for existing tickets that overlap this ticket's intent.

```
DEDUP_SEARCH(keywords: <title keywords>)   # adapter → the configured tracker
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
The following ticket will be created in the tracker repo (`config.yaml` → `tracker.repo`).
This action cannot be silently undone.

[Show ticket draft here]

Approve? (yes / no / edit)
```

Do not call the tracker until the user replies with explicit approval ("yes"
or equivalent). A non-answer is not approval.

## Step 3 — Create the ticket(s)

On approval, perform the tracker operations below via the **tracker adapter**
(`steps/shared/tracker.md`), which maps each to the configured platform's tools —
this step names no platform-specific tool.

**Single ticket (bug / task / feat):**

```
CREATE_TICKET(
  title:  <title>,
  body:   <filled ISSUE BODY block>,
  labels: [type:<type>, priority:<P0-P3>, area:<area>],
  type:   <Bug|Feature|Task>,   # SET_TYPE — falls back to the type:<…> label where the platform lacks native types
)
```

**Epic (parent + child stubs):**

1. `CREATE_TICKET` the **Epic parent** (`type: Epic`); capture its id `<E>`.
2. `CREATE_TICKET` each **child stub** (its own body + labels/type); capture each id `<C>`.
3. `ADD_SUB_ISSUE(parent: <E>, child: <C>)` for every child — the tracker then
   renders the child checklist + progress rollup on the Epic.

**Board / project fields** (Priority / Effort / Status) are `SET_FIELDS`. On some
platforms (e.g. GitHub Projects v2) these are not set at create time and may be a
manual step — see the adapter. Do not block creation on them.

## Output

- **Ticket id(s)** — the assigned identifier(s) per the configured id-scheme
  (`config.yaml` → `id_scheme`; the tracker ticket number(s)). An epic returns the
  parent id plus each linked child id.
- Hand a single ticket (or a chosen epic child) to `/flow-start` to begin Shape.
  The Epic parent itself is a tracking umbrella — Shape runs per child.

## Notes

- The worklog directory `docs/flow/worklog/<TICKET-ID>/` is created by `steps/shared/kickoff.md`
  once the ticket id is known.
- If creation fails (network error, permissions), report the error and retry once
  before escalating to the user.
