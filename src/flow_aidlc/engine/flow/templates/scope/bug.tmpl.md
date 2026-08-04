<!--
FLOW SCOPE TEMPLATE — BUG
Consumed by .flow/steps/scope/story.md when the clarified ticket type is `bug`.
The block between the ISSUE BODY markers becomes the tracker issue body; the
NATIVE FIELDS block is set by scope/publish in the tracker sidebar (labels, issue
type, board fields, milestone) and is NOT typed into the body.
Fill every <placeholder>; delete the "(optional …)" line if the value is unknown.
Mirrors the canonical "Scope Ticket Templates" reference (Bug tab).
-->

<!-- ===== ISSUE BODY ↓ ===== -->
### What's wrong
<plain description of the problem>

### Steps to reproduce
1. ...
2. ...
3. ...

### Acceptance Criteria
- [ ] AC1: <observable, testable outcome that proves this is fixed>
- [ ] AC2: <...>

### Non-Goals / Out of Scope
- <explicitly not covered by this fix>

### Area
<an existing area label from the tracker>

### Affected file(s)/module(s)  (optional — fill in if known)
- <path/to/file:line>

### Severity
<P0 | P1 | P2 | P3> — <one-line plain description, e.g. "major, blocks a workflow">
> Keep this the SAME value as the Priority label and the Priority field in the
> sidebar — don't let body severity, the priority label, and the Priority field
> drift into three different answers.

### Where did you see it?
<environment where the problem was observed>

### Version / commit
<version string or commit SHA>

### Flags
- [ ] A fix will likely require a database migration
<!-- ===== ISSUE BODY ↑ ===== -->

<!-- ===== NATIVE FIELDS (set at scope/publish in the tracker sidebar — not body) =====
Labels    : area:<area>, priority:P<0-3>, type:bug
Type      : Bug
Priority  : <Urgent|High|Medium|Low>   (board field — map from Severity: P0→Urgent, P1→High, P2→Medium, P3→Low)
Effort    : <XS|S|M|L>
Project   : <triage board> → Status: Needs Triage
Milestone : <next patch release>
Parent    : <link if part of a tracker, e.g. a testing-findings tracker>
-->
