<!--
FLOW SCOPE TEMPLATE — FEATURE
Consumed by .flow/steps/scope/story.md when the clarified ticket type is `feat`.
The block between the ISSUE BODY markers becomes the tracker issue body; the
NATIVE FIELDS block is set by scope/publish in the tracker sidebar (labels, issue
type, board fields, milestone) and is NOT typed into the body.
A sharp Why + Non-Goals here is what keeps Shape's requirements draft short and
its question list small. Fill every <placeholder>; delete "(optional …)" if unknown.
Mirrors the canonical "Scope Ticket Templates" reference (Feature tab).
-->

<!-- ===== ISSUE BODY ↓ ===== -->
### Title
<short, imperative feature title>

### Why
<motivation — who asked, what pain point this solves, why now>

### Acceptance Criteria
- [ ] AC1: <observable, testable outcome>
- [ ] AC2: <...>

### Non-Goals / Out of Scope
- <explicitly excluded from this ticket>

### File attachment
<designs / screenshots / spec links, if applicable>

### Area
<an existing area label from the tracker>

### Affected file(s)/module(s)  (optional — fill in if known)
- <real module/service names and files>

### Rough ticket size
<S | M | L>

### Desired target release
<milestone>

### Flags
- [ ] A fix will likely require a database migration
<!-- ===== ISSUE BODY ↑ ===== -->

<!-- ===== NATIVE FIELDS (set at scope/publish in the tracker sidebar — not body) =====
Labels    : area:<area>[, area:<area2>], priority:P<0-3>, type:feature
Type      : Feature
Priority  : <Urgent|High|Medium|Low>   (board field)
Effort    : <S|M|L>   (mirror "Rough ticket size" above)
Milestone : <target release>
Parent    : <link if part of a larger initiative>
-->
