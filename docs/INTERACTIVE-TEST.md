# Interactive lifecycle test — Scope → Shape → Build → Ship

A manual acceptance checklist for the **interactive** path that only runs inside a
live Claude Code session: the `/flow-*` slash commands, the per-phase subagents,
the tracker MCP, and the superpowers / pr-review-toolkit skill packs. The offline
`flow check` gate cannot exercise any of this — this document does.

Run it once against a throwaway repo before publishing, and after any change to the
engine's commands, agents, step guides, or playbook.

> Legend for each step: **Type** = what you enter in Claude Code · **Expect** = what
> should happen · **Verify** = the artifact/state to confirm (exact paths). Tick the
> box when the step passes; record failures in the results table at the bottom.

---

## 0. Prerequisites (install once, not per-repo)

In the Claude Code environment you'll run the test from:

- [ ] `/plugin install superpowers` — the skills Flow invokes (brainstorming, TDD, plan-writing, review)
- [ ] `/plugin install pr-review-toolkit` — the Ship branch-hardening review agents
- [ ] `uv tool install "graphifyy[mcp]"` — the code-graph backend (or run `flow setup` later)
- [ ] `flow` CLI on PATH — `pipx install <path>/dist/flow_aidlc-0.1.0-py3-none-any.whl`
- [ ] A tracker you can write to. Default is **GitHub Issues**; have a scratch repo and a
      token ready. (Jira/Linear/etc. work too — set `--tracker` at init.)

---

## 1. Set up the test repo

```bash
# a small repo with a little real code (so brownfield mapping has something to chew on)
mkdir flow-lifecycle-test && cd flow-lifecycle-test && git init
printf 'def total(items):\n    return sum(i.price for i in items)\n' > billing.py
git add -A && git commit -m "seed"

flow init --repo <you>/flow-lifecycle-test    # scaffolds .flow/, .claude/, knowledge/, .mcp.json
flow setup                                     # graph tool + build + doctor
```

- [ ] `flow init` created `.flow/`, `.claude/`, `knowledge/`, `.mcp.json`, `CLAUDE.md`
- [ ] Put the tracker token where `.env.example` / `.mcp.json` expect it (e.g. `GITHUB_*`)
- [ ] **`flow doctor`** → hooks installed, MCP reachable, code graph wired, **credentials resolve**.
      Do not proceed until doctor is clean (or knowingly-degraded, e.g. no graph → grep fallback).

Now **open Claude Code in this repo.** The rest runs in the session.

---

## 2. Scope — create the ticket

Two entry points; use **2a** if you have no ticket yet (the common case).

### 2a. `/flow-scope`
- [ ] **Type:** `/flow-scope "add a read-only endpoint that lists customers over their credit limit"`
- [ ] **Expect:** `scope-clarify` runs `superpowers:brainstorming`, asks clarifying questions
      **one at a time**, and proposes a **ticket type** (`bug | task | feat | epic`) for you to confirm.
- [ ] **Expect:** `scope-story` drafts the ticket (title, problem/why-now, checkbox acceptance
      criteria, `type`/`priority`/`area` labels) — held in memory, nothing written yet.
- [ ] **CHECKPOINT (publish):** `scope-publish` deduplicates, shows the full draft, and **waits**.
      A non-answer must not create anything.
- [ ] **Type:** `/flow-approve`
- [ ] **Verify:** a real ticket exists in the tracker; Claude reports the assigned id
      (`TASK-<n>` by default, or your tracker's number). Record it as **`<ID>`** below.

> Epic variant (optional): scope an idea big enough to classify as `epic` and confirm
> `scope-publish` creates a parent **plus** linked child sub-issues.

---

## 3. Shape — requirements → design → slices

- [ ] **Type:** `/flow-start <ID>`
- [ ] **Expect:** `shape-intake` runs `VERIFY_EXISTS` against the tracker. A **bogus** id must
      **STOP and scaffold nothing** (worth testing once: `/flow-start TASK-99999` → refuses).
- [ ] **Verify:** `worklog/<ID>.../` scaffolded (`progress.md`, `journal.md`, `questions/`,
      `shape/`, `build/`, `ship/`).

**Conditional pre-steps** (intake routes to these):
- [ ] **Brownfield** (this test touches `billing.py`) → `shape-map` runs **graph-first**
      (`WHO_CALLS`/`NEIGHBORS`/`HUBS`, cited by `file:line`; grep only as fallback).
      **Verify:** `worklog/<ID>.../shape/map-existing.md` lists contracts, callers/dependents,
      and a don't-change list. *(No checkpoint — flows straight on.)*
- [ ] **New dependency** (only if your idea needs one) → **CHECKPOINT (research):** `shape-research`
      runs `deep-research`, writes `worklog/<ID>.../shape/research.md` (options + recommendation +
      **governance screen**), and waits. `/flow-approve` to continue. Nothing is installed.

**Requirements → Design → Slicing:**
- [ ] **CHECKPOINT (requirements):** `superpowers:brainstorming` surfaces FRs/NFRs/edge cases;
      optional guardrail opt-ins (`security-baseline`, `resiliency-baseline`, `test-coverage`) are
      offered. **Verify:** `worklog/<ID>.../shape/requirements.md`; any enabled guardrails recorded
      under `## Guardrails` in `progress.md`. → `/flow-approve`
- [ ] **CHECKPOINT (design):** **Verify:** `worklog/<ID>.../shape/design.md` (approach, components,
      data flow, trade-offs) and — for any cross-cutting decision — a graduated record at
      `knowledge/decisions/NNNN-<slug>.md` linked under `## Graduated decisions`. → `/flow-approve`
- [ ] **(slicing — no checkpoint):** **Verify:** `worklog/<ID>.../shape/slices.md` with columns
      `id, scope, files, order, requirements`; every slice references ≥1 requirement id; slices
      are ordered (foundations first). At the Shape→Build boundary, `checkpoint-reviewer` also
      checks **traceability** (no orphan requirement).

---

## 4. Build — per slice (repeat for each slice in `slices.md`)

- [ ] **Type:** `/flow-slice`  (picks the next unstarted slice from `slices.md`)
- [ ] **(slice-design — no checkpoint):** **Verify:** `worklog/<ID>.../build/<slice>/design.md`
      (signatures, edge cases, acceptance criteria).
- [ ] **CHECKPOINT (code-plan):** `build-plan` runs `superpowers:writing-plans`. **Verify:**
      `worklog/<ID>.../build/<slice>/code-plan.md` has a `## Steps` section (checkboxes per file,
      migrations first) and a `## Tests` section (last); no code written yet. → `/flow-approve`
- [ ] **(generate — no checkpoint):** `build-generate` runs `superpowers:test-driven-development`.
      **Expect:** test-first, one checkbox at a time; the **scope guard** refuses any file not in
      the slice's `slices.md` file list (raises a flag in `journal.md`). **Verify:** source files
      written, every checkbox in `code-plan.md` checked, the suite is **green**.
- [ ] **CHECKPOINT (verify):** the conductor dispatches `guardrail-verifier` (per-rule
      compliant/non-compliant/N-A against the diff — **blocks on any non-compliant**), invokes
      `superpowers:requesting-code-review` + `verification-before-completion`, then dispatches the
      read-only `checkpoint-reviewer`. **Verify:** `worklog/<ID>.../build/<slice>/verify.md` — all
      guardrails passed, review concerns addressed. → `/flow-approve`
- [ ] Repeat until every slice in `slices.md` is checked complete in `progress.md`.

> Guardrail-block test (recommended once): author a trivial always-on guardrail
> (`flow guardrail add no-print` with a rule the slice violates), re-run the slice, and
> confirm `guardrail-verifier` returns **BLOCKED** and the verify checkpoint will not clear.

---

## 5. Ship — branch-hardening → learnings → open-PR (terminal in controlled mode)

- [ ] **Type:** `/flow-ship`
- [ ] **CHECKPOINT (branch-hardening):** the `pr-review-toolkit` agents named in
      `config.yaml → review.branch_hardening` run on the **whole branch diff** (code review,
      silent-failure, test-analysis, type-design, comments). **Verify:** findings addressed or
      dispositioned. → `/flow-approve`
- [ ] **(learnings — no checkpoint):** the pre-PR retro. **Verify:** correction/redirection
      signals captured (later surfaced by `flow learnings`).
- [ ] **CHECKPOINT (open-pr):** `superpowers:finishing-a-development-branch` runs the pre-PR sanity
      checks, then **waits** before `OPEN_PR`. → `/flow-approve`
- [ ] **Verify:** a PR is opened against `config.vcs.base`, body references the ticket
      (`Fixes <ID>`). **Flow STOPS here** — it does **not** merge, close the ticket, or release any
      lock. That's the team's job on the host (branch protection is authoritative).

---

## 6. Cross-cutting commands (spot-check any time)

- [ ] `/flow-status <ID>` (or `flow status`) → shows the ticket's position in Scope→Shape→Build→Ship.
- [ ] `/flow-resume <ID>` mid-run (after a checkpoint) → reconstructs state from `progress.md` and
      continues at the right stage (test this after deliberately closing/reopening the session).
- [ ] `/flow-refresh` → dispatches `curator` to verify `knowledge/map/` invariants against code;
      structure is re-derived from the graph (no STALE flags).
- [ ] `/flow-decide` → records an ad-hoc decision into `knowledge/decisions/`.
- [ ] `/flow-changes` → summarizes the working-tree changes for the current task.

---

## 7. Auto mode (optional — only if you want to test the autonomous path)

> Runs **no human stops**; adversarial panels replace `/flow-approve` and it merges on green CI.
> Test in a **disposable** repo with branch protection + a CI that runs `flow check`.

- [ ] Label a scoped ticket with `config.yaml → execution.label` (default `flow-auto`).
- [ ] **Type:** `/flow-auto <ID>` (single ticket) — confirm each `checkpoint: yes` stage is cleared
      by a panel (`steps/auto/panel-review.md`), not a human.
- [ ] **Merge-on-green:** with green CI, the PR merges and the loop pulls the next labeled ticket.
- [ ] **Park-on-fail:** force a panel non-convergence (or a red gate) → the task becomes a draft PR
      + `flow-blocked`, and the loop continues rather than blocking.
- [ ] **Kill switch:** `touch .flow/STOP` → the loop halts before the next ticket.
- [ ] **Cap:** confirm it stops after `execution.max_tasks`.

---

## Results

| Stage | Checkpoint | Pass | Notes |
|-------|-----------|------|-------|
| Scope / publish | yes | ☐ | ticket id: |
| Shape / map-existing | no | ☐ | brownfield only |
| Shape / research | yes | ☐ | dependency only |
| Shape / requirements | yes | ☐ | |
| Shape / design | yes | ☐ | + graduated decisions |
| Shape / slicing | no | ☐ | traceability clean |
| Build / slice-design | no | ☐ | |
| Build / code-plan | yes | ☐ | `## Steps` + `## Tests` |
| Build / generate | no | ☐ | scope guard held; suite green |
| Build / verify | yes | ☐ | guardrails + review |
| Ship / branch-hardening | yes | ☐ | pr-review-toolkit |
| Ship / learnings | no | ☐ | |
| Ship / open-pr | yes | ☐ | PR opened, not merged |
| Auto (optional) | — | ☐ | panel / merge / park / STOP |

**Sign-off:** the interactive lifecycle passes when every checkpoint stopped and waited,
every artifact above exists at its stated path, the scope guard and guardrail block held,
and Ship terminated at an open PR (controlled) without merging.

---

## Teardown

```bash
# delete the scratch tracker ticket/PR, then:
cd .. && rm -rf flow-lifecycle-test
```
