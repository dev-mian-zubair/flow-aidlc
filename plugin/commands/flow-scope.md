---
description: Run the Scope front door for a new idea — clarify → story → (approval) → publish.
argument-hint: "<idea or brief description>"
---

**FRESH RUN — no carried context.** Every `/flow-scope` invocation starts a brand-new Scope run. Before anything else:

- **Disregard any earlier Scope context in this conversation.** Do not reuse, resume, or reference an idea, agreed intent, success criteria, or drafted ticket from a previous `/flow-scope` run. This command always (re)starts at `scope/clarify` from scratch — it is never "continue." Advancing a run is done with `/flow-approve`, not by re-invoking `/flow-scope`; re-invoking abandons any in-progress Scope run and begins a new one.
- **Take the idea only from this invocation** (the argument supplied after the command). If no idea was provided, ask the user for a new idea now — never infer it from earlier conversation.
- If a previous Scope run is visible in this conversation, print exactly once, before starting: `Starting a fresh Scope run — discarding previous Scope context.`

Then read `.flow/playbook.md` and execute the Scope phase front door for the provided idea: dispatch the `scope-clarify` subagent (loading `.flow/steps/scope/clarify.md` and invoking `superpowers:brainstorming`), then `scope-story` (loading `.flow/steps/scope/story.md`), then pause at the `scope/publish` checkpoint and wait for `/flow-approve` before dispatching `scope-publish` (loading `.flow/steps/scope/publish.md`). This phase is repo-less — do not write to the codebase; output goes only to the tracker and the worklog scaffold created by `.flow/steps/shared/kickoff.md`. `scope-clarify` also classifies the idea as `bug | task | feat | epic` (confirmed with you) and, for an epic, decomposes it into one-level child stubs; `scope-story` then fills the matching template(s), and `scope-publish` creates either a single issue or an Epic parent plus child sub-issues linked via the tracker's sub-issue mechanism. Before dispatching `scope-clarify`, confirm the code graph is fresh (rebuild it with the configured `graph.build` command via `flow refresh` if in doubt) so structural grounding via the graph is trustworthy. The Knowledge Map holds **invariants** only — structure comes from the code graph, so there is no structural-freshness tracking — see `.flow/steps/shared/knowledge-map.md`.
