# content-validation

Run these checks before writing any markdown or diagram file to the worklog or
the codebase. A check failure blocks the write.

## Markdown validation

Run markdownlint on the file content before persisting it:

```bash
npx markdownlint-cli2 "<path>"
```

Required passes:

- No bare HTML (`no-inline-html`).
- No duplicate headings at the same level within a file.
- Exactly one H1 (`#`) per file.
- Fenced code blocks have a language tag.
- No trailing spaces; blank line before and after every heading and list.

If the tool is unavailable, perform a manual checklist against the rules above
before writing the file.

## Diagram validation (Mermaid)

For any fenced block tagged ` ```mermaid `:

1. Confirm the diagram type is declared on the first line (e.g., `flowchart LR`,
   `sequenceDiagram`, `erDiagram`).
2. Confirm all node ids are alphanumeric with no spaces.
3. Confirm arrow syntax matches the diagram type (`-->`, `->>`, `||--||`, etc.).
4. If a Mermaid CLI is available: `mmdc -i <file> -o /dev/null` must exit 0.

## Structure validation

Before writing a worklog artifact, confirm:

- The file uses the matching template from `.flow/templates/` as its skeleton.
- All `[Answer]:` placeholders are either filled or intentionally left empty at
  this stage (question files may leave them empty by design).
- No section from the template has been silently deleted; add a `<!-- N/A -->`
  comment if a section does not apply.

## Snapshot status header

Every worklog Shape artifact (`requirements.md`, `design.md`, `slices.md`) must
begin with the following line immediately after its H1:

```
> **Status:** SNAPSHOT · **Owner:** <user> · **Last updated:** <ISO date>
```

Worklog artifacts are point-in-time snapshots of thinking at a given session;
they are not living documents. `knowledge/` docs keep their richer provenance
frontmatter — do not conflate the two. The blockquote does not count as a
heading; exactly one H1 per file is still required.

## Evidence discipline

A claim about the codebase in a Shape artifact must be grounded in one of the
following ways:

- **Cited:** the claim cites a file path opened this session (e.g.
  `src/services/orders.py:142`). This is the required form for any
  claim that drives a design decision.
- **Tagged inference:** the claim is an unverified inference and is tagged
  `(guess)`. Guesses may appear in risks or open questions, but must not drive
  design decisions alone.
- **Neither:** a claim with neither a citation nor a `(guess)` tag must not drive
  a design decision and must be resolved before Shape is approved.

Adopted from `aidlc-scoping`. Anti-hallucination discipline for Shape artifacts.

## On failure

Do not write the file. Report the specific rule that failed and the line or
block that caused it. Fix the content, then re-validate before writing.
