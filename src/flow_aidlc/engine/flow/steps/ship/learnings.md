# learnings

## Goal

Run the learnings retro at the close of a task: extract correction and
redirection signals from the task journal, present candidates to the human,
and append kept practices to `docs/flow/knowledge/practices.md`.

## When to run

After `branch-hardening.md` is approved, before `open-pr.md`. This is the **pre-PR
wrap-up** — it mines the completed task journal, so it runs while finishing the branch,
before the PR is opened. (The Flow ends at `open-pr`; there is no post-merge stage.)

## Steps

### 1 — Extract candidates

Run the learnings extractor against this task's worklog directory, pointing at
the practices store so already-recorded entries are flagged:

```bash
python -m flow_aidlc.checks.learnings docs/flow/worklog/<TICKET-ID> --practices docs/flow/knowledge/practices.md
```

The tool scans `docs/flow/worklog/<TICKET-ID>/journal.md` for correction and redirection
signals (words such as "actually", "instead", "should have", "revert", etc.)
and prints a numbered candidate list. Candidates already present in
`docs/flow/knowledge/practices.md` are marked `[already recorded]`.

### 2 — Present candidates to the human

Show the candidate list as-is. For each candidate:

- **The human decides** — keep or discard.
- The agent proposes context but never auto-appends a judgment call.
- A discarded candidate is simply not appended; no record of it is kept.

If there are no candidates, note that and proceed to `open-pr` — the retro is
still complete.

### 3 — Append kept practices

For each candidate the human approves, use `flow_aidlc.checks.learnings.append_practice`
to append it to `docs/flow/knowledge/practices.md`. The idempotency marker ensures a
practice is never duplicated across retros.

If a candidate is really an **architectural decision** (a one-way door with
lasting structural implications), route it to `docs/flow/knowledge/decisions/` using the
format in `steps/shared/decision-format.md` instead of appending it as a
practice.

For the journal entry format that is the source of candidates, see
`steps/shared/journal-format.md`.

### 4 — Commit

Commit the updated `docs/flow/knowledge/practices.md` (if any practices were appended):

```
docs(flow): capture learnings from <TICKET-ID>
```

Include in the body which practices were added and why they were kept.

### 5 — Note: feeds forward via kickoff

`steps/shared/kickoff.md` instructs every new task to read `docs/flow/knowledge/practices.md`
if present. Practices appended here automatically inform every future task's
kickoff — no further wiring is needed.

## Output

- `docs/flow/knowledge/practices.md` updated with any kept practices (idempotent).
- Commit `docs(flow): capture learnings from <TICKET-ID>` if practices were added.
- Discarded candidates are not recorded anywhere.
