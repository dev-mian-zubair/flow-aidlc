# Scope / clarify

Turn a raw idea into structured intent before writing a single line of code or a
ticket.

## Purpose

Extract the real goal, surface ambiguity, and agree on what success looks like.
No repo access, no worklog — this step produces only a question file.

## Powered by superpowers

Invoke `superpowers:brainstorming` now. Let it explore the idea freely before
committing to any framing.

```
/superpowers:brainstorming
```

Use the brainstorming output to identify:

- The core user or system need.
- What "done" looks like (observable outcome, not implementation).
- Constraints: time-box, tech limits, out-of-scope boundaries.
- Open questions that must be answered before story-writing can proceed.

## Clarify open questions

For every open question that cannot be resolved in the current conversation,
ask it inline in the chat. This step is **repo-less and worklog-less** — no
files are written to the repository. If a durable record is needed, capture
the answer in a ticket comment after the task id is assigned.

Questions stay in the conversation — never silently skip an unresolved blocker.

Apply `steps/shared/overconfidence-prevention.md` when deciding whether to ask
vs infer — never proceed past unresolved ambiguity.

## Output

A shared understanding of:

- **Intent:** one sentence stating the goal.
- **Success criteria:** two to five observable outcomes.
- **Constraints:** what is explicitly out of scope.
- **Open questions:** captured in the question file (may be empty if none remain).

Hand off to **Scope / story** once intent is agreed and any blocking questions
are answered.

## Notes

- This step is **repo-less** — do not read or modify any source file.
- Do not create a worklog entry; the worklog is created in `steps/shared/kickoff.md`
  only after a task id is assigned (Scope / publish).
