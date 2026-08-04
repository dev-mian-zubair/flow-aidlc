<!--
FLOW SCOPE TEMPLATE — EPIC (parent)
Consumed by .flow/steps/scope/story.md when the clarified ticket type is `epic`.
An epic is a tracking umbrella: this file is the PARENT issue body; each child is
drafted from feature.tmpl.md / small-task.tmpl.md as a thin STUB and linked as a
tracker sub-issue at scope/publish (sub-issue link). Children are fleshed out
later in their own Shape phase — do NOT over-specify them here.
Mirrors the canonical "Scope Ticket Templates" reference (hybrid epic model).
-->

<!-- ===== ISSUE BODY ↓ ===== -->
### Goal
<the umbrella outcome this epic delivers — one short paragraph, and who it's for>

### Why now
<motivation — the initiative-level driver>

### Epic-level Acceptance Criteria
- [ ] AC1: <observable outcome true when the whole epic is done>
- [ ] AC2: <...>

### Non-Goals / Out of Scope
- <explicitly excluded from this epic>

### Child tickets
<!-- publish replaces each line with the real "- [ ] #<n> — <title>" once the
     child sub-issue exists; the tracker then shows the progress rollup. -->
- [ ] <child 1 title>  (feat|task, S|M|L)
- [ ] <child 2 title>  (feat|task, S|M|L)

### Area(s)
<one or more existing area labels from the tracker>

### Desired target release
<milestone>

### Flags
- [ ] One or more children will likely require a database migration
<!-- ===== ISSUE BODY ↑ ===== -->

<!-- ===== NATIVE FIELDS (set at scope/publish in the tracker sidebar — not body) =====
Labels    : area:<area>[, area:<area2>], priority:P<0-3>, type:epic
Type      : Epic        (requires tracker issue types; else the type:epic label carries it)
Priority  : <Urgent|High|Medium|Low>   (board field)
Milestone : <target release>
Children  : each linked via the tracker's sub-issue mechanism (parent: <this epic #>, child: <child #>)
-->
