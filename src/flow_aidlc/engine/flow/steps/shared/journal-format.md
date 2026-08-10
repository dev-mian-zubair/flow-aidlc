# journal-format

The journal is the append-only record of everything that happened during a task.

## File location

```
docs/flow/worklog/<TICKET-ID>/journal.md
```

One file per task. Never split across multiple files.

## Entry format

```
## <ISO-8601 datetime>

<raw user input or agent note, verbatim>
```

Example:

```
## 2026-08-03T14:22:05Z

Decided to use the existing BudgetService rather than a new one.
Risk: budget cache invalidation must be explicit. See decision 0042.
```

## Rules

- **Append only.** Never edit, reword, or delete an existing entry.
- **ISO-8601 datetime** in the heading, UTC preferred (`Z` suffix).
- **Raw input verbatim.** If the user types something, record exactly what they
  typed. Do not summarise or paraphrase.
- Agent-generated notes (decisions reached, blockers, handoffs) are also
  appended as entries; prefix the content with `[agent]` to distinguish.
- The journal is not a summary document — it is a log. Readers use
  `steps/shared/resume.md` to extract the relevant tail.
- An empty journal (`touch docs/flow/worklog/<TICKET-ID>/journal.md`) is valid at task start.
