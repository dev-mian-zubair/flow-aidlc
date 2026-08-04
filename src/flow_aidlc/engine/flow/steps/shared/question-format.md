# question-format

Questions in the Flow are on-disk files, never inline chat prompts.

## File location

Write question files to the `questions/` subdirectory of the task worklog:

```
worklog/<PI-NNN>/questions/<stage>.questions.md
```

Examples:

```
worklog/<PI-NNN>/questions/requirements.questions.md
worklog/<PI-NNN>/questions/design.questions.md
```

Name the file `<stage>.questions.md` (dot-separated, not hyphenated) inside
`worklog/<PI-NNN>/questions/`.

## File structure

```markdown
# Questions — <Stage Name>

<!-- One block per question. -->

## Q1: <Short question title>

<Full question text. One or two sentences. Be specific.>

Options (if multiple-choice):

- A. <option>
- B. <option>
- C. <option>

[Answer]:
```

## Rules

- Every question block ends with a bare `[Answer]:` line — the human or an
  upstream agent fills in the answer on that line, nothing else.
- Never ask questions inline in the chat. Write the file, then pause and say:
  `Questions written to <path>. Please fill in [Answer]: fields and resume.`
- Do not proceed past a question file until every `[Answer]:` line is non-empty.
- Do not alter any `[Answer]:` line after it has been filled.
- A free-text answer is valid; multiple-choice is a convenience, not a constraint.
