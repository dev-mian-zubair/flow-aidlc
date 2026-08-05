<!--
FLOW SCOPE TEMPLATE — SMALL TASK
Consumed by .flow/steps/scope/story.md when the clarified ticket type is `task`.
The shortest of the three — deliberately trimmed. The block between the ISSUE
BODY markers becomes the tracker issue body; the NATIVE FIELDS block is set by
scope/publish in the tracker sidebar and is NOT typed into the body.
If it needs more than a one-line title, it isn't a small task yet — reclassify.
Mirrors the canonical "Scope Ticket Templates" reference (Small Task tab).
-->

<!-- ===== ISSUE BODY ↓ ===== -->
### Title
<one-line, unambiguous task>

### Exact change requested
<precise, narrow description — no interpretation needed>

### Acceptance Criteria
- [ ] AC1: <the one thing that must be true when this is done>

### Affected file(s)
- <single file, or a very short explicit list>

### Flags
- [ ] A fix will likely require a database migration
- [ ] Do this automatically (proposed flag — automation-eligible; whether this
      shortens or skips Shape's gates is still undecided)
<!-- ===== ISSUE BODY ↑ ===== -->

<!-- ===== NATIVE FIELDS (set at scope/publish in the tracker sidebar — not body) =====
Labels    : area:<area>, priority:P<0-3>, type:task
Type      : Task
Priority  : <Urgent|High|Medium|Low>   (board field)
Effort    : <XS|S>
Milestone : <usually none needed>
Assignee  : Unassigned — automation-eligible when "Do this automatically" is checked
-->
