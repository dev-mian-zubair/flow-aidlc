---
description: Run the Scope front door for a new idea — clarify → story → (approval) → publish.
argument-hint: "<idea or brief description>"
---

Read `.flow/playbook.md`, then execute the Scope phase front door for the provided idea: dispatch the `scope-clarify` subagent (loading `.flow/steps/scope/clarify.md` and invoking `superpowers:brainstorming`), then `scope-story` (loading `.flow/steps/scope/story.md`), then pause at the `scope/publish` checkpoint and wait for `/flow-approve` before dispatching `scope-publish` (loading `.flow/steps/scope/publish.md`). This phase is repo-less — do not write to the codebase; output goes only to tracker and the worklog scaffold created by `.flow/steps/shared/kickoff.md`.
