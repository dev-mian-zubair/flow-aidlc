# Design — Flow execution modes (`controlled` / `auto`)

**Date:** 2026-08-08
**Status:** Approved (brainstorming) — ready for implementation planning
**Topic:** A second execution mode for Flow — `auto` — that replaces human
checkpoints with adversarial reviewer panels, merges on green CI, and grinds a
labeled backlog autonomously. Plus a companion section wiring **Impeccable** as
the design-quality lens.

---

## 1. Problem

Flow today runs one way: **fully controlled** — gated Scope→Shape→Build→Ship with
a human `/flow-approve` at each `checkpoint: yes` stage, terminating at open-PR
("the team owns the merge"). That is the right default for high-stakes work, but
it cannot run unattended. We want an **`auto`** mode: no human stops, agent panels
gate each stage, the PR is opened *and* merged (safely), and the loop picks up the
next task — "a proper engineer grinding the backlog."

## 2. Goals

- Add an **`auto`** mode alongside the existing (now-named) **`controlled`** mode.
- In `auto`, replace each human checkpoint with an **adversarial reviewer panel +
  fix-loop** that round-trips until the artifact settles.
- Extend Ship past open-PR to **merge on green CI**, then pull the **next
  `flow-auto`-labeled ticket** and repeat.
- Keep it **runaway-safe**: green-CI merge gate, park-on-fail, hard caps, a
  kill-switch, and a hard precondition that CI exists.
- Change **nothing** about controlled mode (strictly additive; controlled stays
  the default).

## 3. Non-goals (YAGNI)

- No global "make everything auto" config toggle — auto is only ever an explicit
  `/flow-auto`.
- No skipping of any quality gate in auto (auto = no *human* stop, not no checks).
- No new code-review agents — the code-gate panels reuse `pr-review-toolkit`.
- No autonomous *merge to a protected main without green CI* — refused by design.
- Impeccable: only its **validation + UI-generation** commands (not `live` mode,
  `worlds`/dice, or deep `DESIGN.md`/`PRODUCT.md` standards authoring).

## 4. Decisions captured during brainstorming

| Decision | Choice |
|---|---|
| Auto-merge gate | **Green CI required** (PR's required checks pass; branch protection respected) |
| Review loop | **Adversarial reviewer panel at every checkpoint** + fix-loop to a round cap |
| Next-task source | **Tracker backlog** filtered by the `flow-auto` label, priority order |
| Mode trigger | **Explicit `/flow-auto`** — no global toggle; existing commands stay controlled |
| Task can't settle | **Park it** (draft PR + `flow-blocked`), keep grinding; report parked at end |
| Panel composition | **Stage-typed**; code gates reuse **pr-review-toolkit** (+ guardrail-verifier), UI slices add **Impeccable** |

## 5. The two modes

- **`controlled` (default, unchanged):** human `/flow-approve` at every
  `checkpoint: yes`; terminates at open-PR.
- **`auto` (`/flow-auto`):** no human stops; each checkpoint → adversarial panel +
  fix-loop; Ship → open-PR → **merge on green CI** → next `flow-auto` ticket;
  park-on-fail; capped.

**Invariant:** `auto` runs **every** gate `controlled` runs (guardrails,
`flow check`, branch-hardening). It removes the human stop and *adds* review rigor
+ auto-merge. It never skips a gate.

## 6. Control surface & safety rails

- `/flow-auto` — grind the backlog (`flow-auto`-labeled tickets, priority order).
- `/flow-auto <id>` — one ticket, autonomously.
- Every existing command stays **controlled**. **No** global auto toggle.
- **`config.yaml → execution:`** holds *defaults only* (§9): the label, caps,
  panel size, round cap, merge gate, optional integration branch.
- **Kill-switch:** a `.flow/STOP` sentinel file — checked between every task **and**
  every stage → graceful halt after the current unit. (Also a `flow-stop` tracker
  label honored between tasks.)
- **CI precondition:** `/flow-auto` **refuses to run without a CI workflow**
  (`flow ci init` done). Green CI is the merge backstop; no CI ⇒ no safe
  auto-merge. Surfaced by a `flow doctor`/precondition check.

## 7. Autonomous stage-gating (replaces human checkpoints)

At each `checkpoint: yes` stage, `auto` dispatches a **stage-typed adversarial
panel** on the stage artifact. **Consensus = every panel member clears with no
open high-severity finding** (any member's high-severity finding fails the gate).
On fail → the stage agent revises addressing the findings → re-review; loop to
`review.max_rounds` (default 5). Converge → **auto-advance** (no human).
Cap-without-converge → **park** (§8). Findings below high-severity are recorded
and carried to the final report, not looped on (mirrors the SDD deferred-minor
rule). The `checkpoint-stop` hook is **bypassed** in auto (context-clearing
checkpoints and the resume path are unchanged).

**Stage-typed panel composition:**

| Gate | Artifact | Panel |
|---|---|---|
| Scope/publish, Shape/requirements, Shape/design | prose | `checkpoint-reviewer` + artifact critics (completeness, traceability, ambiguity) |
| Build/code-plan | plan | `checkpoint-reviewer` + a plan critic |
| **Build/verify** | slice **diff** | `guardrail-verifier` + pr-review-toolkit subset (`code-reviewer`, `silent-failure-hunter`, `pr-test-analyzer`, `type-design-analyzer`) **+ Impeccable for UI slices** |
| **Ship/branch-hardening** | branch **diff** | the full `config.review.branch_hardening` set (pr-review-toolkit) + `guardrail-verifier` **+ Impeccable for UI** |

The code-gate panels **are** `config.review.branch_hardening` (a per-slice subset
at Build/verify) — **no new review agents**, and it composes with the
`pr-review-toolkit` prerequisite `flow doctor` already checks.

## 8. Ship in auto mode + failure handling

- Branch-hardening (panel) → learnings → open-PR, no human stop.
- **Two independent merge gates, both must be green:** (a) every in-session
  adversarial panel cleared, and (b) the PR's CI (`flow check` + tests + any
  `--gates`) green. The loop **polls the PR's required checks** via the tracker/VCS
  MCP; red CI → pull failures → fix-loop → re-push → re-poll.
- Merge (respecting branch protection; optional `merge.target` integration branch)
  → ticket auto-closes (`Fixes #`) → loop to next task.
- **Park-on-fail:** panel non-converge at the round cap, or CI still red after
  fixes → leave a **draft PR** + `flow-blocked` label + a comment on *why*, then
  skip to the next backlog task. Never halts the whole run for one stuck task.
- **Outer loop:** pull next `flow-auto` ticket → run the playbook-without-stops →
  merge → repeat **until** queue empty | `max_tasks` | budget | `.flow/STOP`.
- **Final report:** merged / parked / skipped, with PR + ticket links.

## 9. Config schema — `config.yaml → execution:`

```yaml
execution:
  # Defaults for `/flow-auto`. Presence of this block does NOT enable auto —
  # auto only runs when `/flow-auto` is explicitly invoked.
  label: flow-auto            # tracker label that queues a ticket for auto
  max_tasks: 5                # hard cap on tasks per `/flow-auto` run
  budget: null                # optional token/time budget (null = unbounded but capped by max_tasks)
  review:
    panel_size: 3             # adversarial reviewers per prose-gate panel
    max_rounds: 5             # fix-loop rounds before park
  merge:
    gate: green-ci            # only 'green-ci' is supported (the safety model)
    target: ""                # integration branch; empty = vcs.base
  require_ci: true            # /flow-auto refuses without a CI workflow
```

`config-consistency` validates: `merge.gate == green-ci`, `require_ci` is a bool,
and (new check) if an `execution:` block sets auto defaults, a CI workflow exists.

## 10. Companion: Impeccable integration (design quality)

Impeccable (`pbakaus/impeccable`, **Apache-2.0**) is a Claude Code skill pack for
UI design quality. Scope here: **validation + UI generation only.**

- **Setup — opt-in auto-install (not a bare prerequisite).** Unlike
  superpowers/pr-review-toolkit (user-level interactive marketplace plugins),
  Impeccable ships a **non-interactive, project-local** installer, so `flow setup`
  can install it: `flow setup --with-impeccable` runs
  `npx impeccable install --providers=claude --scope=project` (detect `npx`, guide
  if absent — the existing detect-and-guide posture). It writes
  `.claude/skills/impeccable/`; init gitignores its ephemera (`.impeccable/*.png`,
  `sessions/`, `previews/`, `cache/`, `config.local.json`).
- **Touchpoints (validation + UI generation only):**
  - **Build/generate** (UI slice): the phase agent may use the generation commands
    (`/impeccable craft|polish|distill|typeset|layout|colorize|…`) to produce/refine UI.
  - **Build/verify + auto-mode panel** (UI slice): validation via `/impeccable audit`
    + `/impeccable critique`, and the deterministic `npx impeccable detect --json .`
    — Impeccable is the **design-quality lens** in the §7 panel for UI slices.
  - **CI gate:** `flow ci init --gates impeccable` emits an
    `npx impeccable detect --json .` step (exit-code gated), beside semgrep/conftest.
  - **`flow doctor`:** optional/frontend detection — is `.claude/skills/impeccable/`
    present? WARN-only, only relevant when the repo builds UI.
- **Out of scope:** `live` mode, `worlds`/dice, deep `DESIGN.md`/`PRODUCT.md`
  standards authoring.

## 11. Implementation surface

Most of `auto` is **engine methodology (prose)**, not Python:

- `playbook.md` — a **"Execution modes"** section defining per-mode stage behavior
  (controlled = human stop; auto = panel + fix-loop).
- New `steps/auto/*` guides — the outer loop, the stage-typed panel review, the
  poll-and-merge, park-on-fail, the final report.
- `steps/build/*` + `steps/ship/branch-hardening.md` — the stage-typed panels;
  Ship gains the poll-and-merge path (auto only).
- New `/flow-auto` command (`engine/claude/commands/` + regenerated plugin).
- `checkpoint-stop` hook — bypass in auto.
- Impeccable touchpoints in `steps/build/generate.md`, `verify.md`,
  `branch-hardening.md`, INTEGRATIONS.

**Thin Python/CLI surface:** the `execution:` config block + defaults; a
precondition check (`flow doctor`: CI configured? tracker write scope? — WARN/FAIL);
config-consistency validation of the `execution:` block; `flow ci init --gates
impeccable`; `flow setup --with-impeccable`; init gitignore additions.

## 12. Testing

- **Python/CLI (unit-testable):** `execution:` config parsing + defaults;
  config-consistency validation (merge.gate, require_ci, CI-exists-if-auto);
  `flow ci init --gates impeccable` emits the detect step; `flow setup
  --with-impeccable` invokes the installer (mock `npx` via PATH; `--dry-run`
  writes nothing); `flow doctor` auto-precondition line; init gitignores
  Impeccable ephemera.
- **Engine assets (structural):** `guardrail_lint`/`structure_check`/
  `config-consistency`/`reference-selfcheck` stay green with the new
  playbook/steps/agents; the `/flow-auto` command + panel agents lint clean;
  plugin regenerates.
- **Not unit-tested:** agent runtime behavior (the panels, the loop) — that's
  methodology prose exercised by a real `/flow-auto` run, not pytest.

## 13. Files touched

- **Engine (new):** `steps/auto/{loop,panel-review,merge,report}.md`,
  `claude/commands/flow-auto.md`, panel/critic agents under `claude/agents/`.
- **Engine (modified):** `playbook.md`, `steps/build/{generate,verify,code-plan}.md`,
  `steps/ship/branch-hardening.md` + `open-pr.md`, `config.tmpl.yaml`
  (`execution:` block), `claude/hooks/checkpoint-stop.sh`, `INTEGRATIONS.md`.
- **CLI/Python (modified):** `commands/setup.py` (`--with-impeccable`),
  `commands/ci.py` (`impeccable` gate), `commands/doctor.py` (auto precondition +
  optional Impeccable detection), `commands/init.py` (gitignore ephemera),
  `checks/config_consistency.py` (`execution:` validation).
- **Tests:** `test_ci.py`, `test_setup.py`, `test_doctor.py`, `test_init.py`,
  `test_config_consistency.py`.
- **Plugin:** regenerated (`flow plugin build`).

## 14. Acceptance

1. `controlled` mode behaves exactly as today (regression: existing tests green).
2. `/flow-auto` refuses without a CI workflow; with CI, it runs the backlog loop:
   pulls `flow-auto` tickets, gates each stage with a stage-typed panel, opens +
   merges each PR **only on green CI**, and continues to the next.
3. A task that can't settle is parked (draft PR + `flow-blocked`) and the loop
   continues; a final report lists merged/parked.
4. `.flow/STOP` halts the loop after the current unit; `max_tasks` caps the run.
5. `flow ci init --gates impeccable` emits the detect step; `flow setup
   --with-impeccable` installs the skill non-interactively; init gitignores its
   ephemera; `flow doctor` shows the auto precondition + optional Impeccable line.
6. Full suite green; engine lints clean; plugin regenerates without drift.

## 15. Build phases (for the plan)

1. **Config + preconditions** — `execution:` block, config-consistency validation,
   `flow doctor` auto precondition. (Thin, testable.)
2. **`/flow-auto` + the outer loop + park/report** — command + `steps/auto/*`.
3. **Stage-typed panels** — playbook "Execution modes" + Build/verify +
   branch-hardening panel wiring (reuse pr-review-toolkit).
4. **Ship poll-and-merge** — the green-CI gate + merge + next.
5. **Impeccable integration** — setup auto-install, ci `--gates impeccable`,
   Build touchpoints, doctor detection, init gitignore.
