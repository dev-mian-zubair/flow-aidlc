# Flow Execution Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an `auto` execution mode to Flow — no human checkpoints (adversarial reviewer panels + fix-loop instead), merge-on-green-CI, and an autonomous backlog loop — alongside the unchanged `controlled` default.

**Architecture:** ~20% thin Python/CLI (a `config.yaml → execution:` block, a config-consistency shape check, a `flow doctor` auto-readiness line) + ~80% engine methodology prose (a playbook "Execution modes" section, `steps/auto/*` guides, a `/flow-auto` command, stage-typed panels reusing `pr-review-toolkit`, a Ship poll-and-merge path, a `checkpoint-stop` bypass). Python parts are pytest-TDD; engine parts are authored and verified by structural tests + the existing gate/lint staying green + plugin regeneration.

**Tech Stack:** Python 3.10+ (stdlib + `pyyaml`), pytest (dev); engine assets are Markdown consumed by Claude Code.

## Global Constraints

- Python `>=3.10`; new modules start with `from __future__ import annotations`.
- Stdlib + `pyyaml` only for runtime code (no new deps).
- **Impeccable is OUT of scope for this plan** (it is Plan 2). Panels here reuse only `pr-review-toolkit` + `guardrail-verifier`.
- `controlled` mode behavior is **unchanged** — strictly additive; the full existing suite must stay green.
- `auto` runs **every** gate `controlled` runs; it removes the human stop and adds review rigor + auto-merge. It never skips a gate.
- Auto-merge gate is **green-ci only** (`execution.merge.gate == "green-ci"`).
- No global auto toggle — auto runs only via the explicit `/flow-auto` command.
- Kill-switch is the `.flow/STOP` sentinel file; task cap is `execution.max_tasks` (default 5); review round cap is `execution.review.max_rounds` (default 5).
- Engine markdown must not introduce dangling ADR refs (`decisions/NNNN` / `ADR NNNN`) — `tests/test_no_dangling_adr_refs.py` guards this.
- Tests run via `uv run --with pytest --with pyyaml python -m pytest -q` when pytest isn't on PATH.
- JSON/YAML edits preserve existing comment-preserving conventions (targeted line edits, not full round-trips) where the codebase already does so.
- Reference spec: `docs/superpowers/specs/2026-08-08-flow-execution-modes-design.md`.

---

## File Structure

- **`src/flow_aidlc/engine/flow/config.tmpl.yaml`** — add the `execution:` defaults block. (Task 1)
- **`src/flow_aidlc/checks/config_consistency.py`** — add check C8 (execution block shape). (Task 2)
- **`src/flow_aidlc/commands/doctor.py`** — add `_check_auto` (auto-readiness line). (Task 3)
- **`src/flow_aidlc/engine/claude/commands/flow-auto.md`** (new) + **`src/flow_aidlc/engine/flow/steps/auto/loop.md`** (new) — the `/flow-auto` command + outer loop. (Task 4)
- **`src/flow_aidlc/engine/flow/playbook.md`** + **`steps/auto/panel-review.md`** (new) + **`steps/build/verify.md`** + **`steps/ship/branch-hardening.md`** — the "Execution modes" section + stage-typed panels. (Task 5)
- **`steps/ship/open-pr.md`** + **`steps/auto/merge.md`** (new) + **`steps/auto/report.md`** (new) + **`claude/hooks/checkpoint-stop.sh`** — Ship poll-and-merge + report + hook bypass. (Task 6)
- **Tests:** `tests/test_init.py`, `tests/test_config_consistency.py`, `tests/test_doctor.py`, `tests/test_execution_modes.py` (new, structural).

---

## Task 1: `execution:` config block

**Files:**
- Modify: `src/flow_aidlc/engine/flow/config.tmpl.yaml`
- Test: `tests/test_init.py`

**Interfaces:**
- Produces: an `execution:` mapping in every rendered `.flow/config.yaml` with keys `label`, `max_tasks`, `budget`, `review.{panel_size,max_rounds}`, `merge.{gate,target}`, `require_ci`.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_init.py
def test_init_renders_execution_block(tmp_path):
    import subprocess, yaml
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    from flow_aidlc.commands import init
    assert init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)]) == 0
    cfg = yaml.safe_load((tmp_path / ".flow" / "config.yaml").read_text())
    ex = cfg["execution"]
    assert ex["merge"]["gate"] == "green-ci"
    assert ex["max_tasks"] == 5
    assert ex["review"]["max_rounds"] == 5
    assert ex["require_ci"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_init.py::test_init_renders_execution_block -q`
Expected: FAIL with `KeyError: 'execution'`.

- [ ] **Step 3: Add the block to the config template**

Append to `src/flow_aidlc/engine/flow/config.tmpl.yaml` (after the `graph:` block, at top level):

```yaml
execution:
  # Defaults for `/flow-auto` (auto mode). Presence here does NOT enable auto —
  # auto runs only when you explicitly invoke `/flow-auto`. controlled is default.
  label: flow-auto            # tracker label that queues a ticket for auto
  max_tasks: 5                # hard cap on tasks per `/flow-auto` run
  budget: null                # optional token/time budget (null = capped only by max_tasks)
  review:
    panel_size: 3             # adversarial reviewers per prose-gate panel
    max_rounds: 5             # fix-loop rounds before a task is parked
  merge:
    gate: green-ci            # only 'green-ci' is supported (the safety model)
    target: ""                # integration branch; empty = vcs.base
  require_ci: true            # `/flow-auto` refuses without a CI workflow
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_init.py -q`
Expected: PASS (existing init tests + the new one).

- [ ] **Step 5: Commit**

```bash
git add src/flow_aidlc/engine/flow/config.tmpl.yaml tests/test_init.py
git commit -m "feat(modes): execution: config block (auto-mode defaults)"
```

---

## Task 2: config-consistency check C8 (execution block shape)

**Files:**
- Modify: `src/flow_aidlc/checks/config_consistency.py` (add C8 after C7, before `return errors`)
- Test: `tests/test_config_consistency.py`

**Interfaces:**
- Consumes: the parsed `cfg` dict and `errors` list inside `check()`.
- Produces: C8 error strings for a malformed `execution:` block.

- [ ] **Step 1: Write the failing tests**

```python
# add to tests/test_config_consistency.py
def test_c8_bad_merge_gate_blocks(tmp_path):
    root = _make_repo(tmp_path)
    cfg = root / ".flow" / "config.yaml"
    cfg.write_text(cfg.read_text() + "\nexecution:\n  merge:\n    gate: yolo\n")
    errs = check(root)
    assert any("C8" in e and "green-ci" in e for e in errs), errs

def test_c8_bad_require_ci_type_blocks(tmp_path):
    root = _make_repo(tmp_path)
    cfg = root / ".flow" / "config.yaml"
    cfg.write_text(cfg.read_text() + "\nexecution:\n  require_ci: maybe\n")
    errs = check(root)
    assert any("C8" in e and "require_ci" in e for e in errs), errs

def test_c8_bad_max_rounds_blocks(tmp_path):
    root = _make_repo(tmp_path)
    cfg = root / ".flow" / "config.yaml"
    cfg.write_text(cfg.read_text() + "\nexecution:\n  review:\n    max_rounds: 0\n")
    errs = check(root)
    assert any("C8" in e and "max_rounds" in e for e in errs), errs

def test_c8_valid_execution_block_clean(tmp_path):
    root = _make_repo(tmp_path)
    cfg = root / ".flow" / "config.yaml"
    cfg.write_text(cfg.read_text() +
        "\nexecution:\n  merge:\n    gate: green-ci\n  require_ci: true\n"
        "  max_tasks: 5\n  review:\n    panel_size: 3\n    max_rounds: 5\n")
    errs = check(root)
    assert not any("C8" in e for e in errs), errs
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_config_consistency.py -k c8 -q`
Expected: FAIL — no C8 errors produced yet (the malformed configs pass).

- [ ] **Step 3: Add the C8 check**

In `src/flow_aidlc/checks/config_consistency.py`, insert immediately before `return errors`:

```python
    # ---- C8: execution block shape (auto-mode defaults) --------------------
    execution = cfg.get("execution")
    if execution is not None:
        if not isinstance(execution, dict):
            errors.append("C8 execution: `execution:` must be a mapping")
        else:
            gate = (execution.get("merge", {}) or {}).get("gate")
            if gate is not None and gate != "green-ci":
                errors.append(
                    f"C8 execution.merge.gate: only 'green-ci' is supported (got '{gate}') "
                    "— the auto-merge safety model requires green CI"
                )
            require_ci = execution.get("require_ci")
            if require_ci is not None and not isinstance(require_ci, bool):
                errors.append("C8 execution.require_ci: must be a boolean")
            review = execution.get("review", {}) or {}

            def _pos_int(value: object) -> bool:
                return isinstance(value, int) and not isinstance(value, bool) and value >= 1

            for key in ("panel_size", "max_rounds"):
                val = review.get(key)
                if val is not None and not _pos_int(val):
                    errors.append(f"C8 execution.review.{key}: must be an integer >= 1 (got {val!r})")
            max_tasks = execution.get("max_tasks")
            if max_tasks is not None and not _pos_int(max_tasks):
                errors.append(f"C8 execution.max_tasks: must be an integer >= 1 (got {max_tasks!r})")
```

Also document C8 in the module docstring's "Checks:" list (one line): `C8 (execution): the auto-mode 'execution:' block, if present, has a valid shape (merge.gate == green-ci, require_ci bool, positive-int caps).`

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_config_consistency.py -q`
Expected: PASS (all, including the 4 new + the existing end-to-end tracker tests — a real `flow init` config now has an `execution:` block and must stay clean).

- [ ] **Step 5: Commit**

```bash
git add src/flow_aidlc/checks/config_consistency.py tests/test_config_consistency.py
git commit -m "feat(modes): config-consistency C8 validates the execution block"
```

---

## Task 3: `flow doctor` auto-readiness line

**Files:**
- Modify: `src/flow_aidlc/commands/doctor.py` (add `_check_auto` + call it in `run()` after `_check_secrets`)
- Test: `tests/test_doctor.py`

**Interfaces:**
- Consumes: `_Report` (`.line(label, status, detail)`, `.any_fail`), `PASS`/`WARN` constants.
- Produces: `_check_auto(rep: _Report, root: Path) -> None` — reports a `auto` line (WARN/PASS only; never FAIL — controlled mode needs none of this).

- [ ] **Step 1: Write the failing tests**

```python
# add to tests/test_doctor.py
def _ci_workflow(tmp_path):
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "flow-check.yml").write_text("name: flow check\n")

def test_check_auto_warns_without_ci(tmp_path, capsys):
    rep = doctor._Report()
    doctor._check_auto(rep, tmp_path)
    out = capsys.readouterr().out
    assert "[WARN]" in out and "auto" in out
    assert rep.any_fail is False

def test_check_auto_pass_with_ci(tmp_path, capsys):
    _ci_workflow(tmp_path)
    rep = doctor._Report()
    doctor._check_auto(rep, tmp_path)
    out = capsys.readouterr().out
    assert "[PASS]" in out
    assert rep.any_fail is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_doctor.py -k check_auto -q`
Expected: FAIL with `AttributeError: _check_auto`.

- [ ] **Step 3: Implement the check**

In `src/flow_aidlc/commands/doctor.py`, add the call in `run()` after `_check_secrets(rep, root)`:

```python
    _check_auto(rep, root)
```

And add the function near `_check_secrets`:

```python
def _check_auto(rep: _Report, root: Path) -> None:
    """Report `/flow-auto` (auto mode) readiness. WARN/PASS only — controlled
    mode (the default) needs none of this; auto needs a green-CI backstop.
    """
    ci_dir = root / ".github" / "workflows"
    ci_present = (ci_dir.is_dir() and any(ci_dir.glob("*.yml"))) or (root / ".gitlab-ci.yml").exists()
    if ci_present:
        rep.line("auto", PASS, "CI workflow present — `/flow-auto` can merge on green CI")
    else:
        rep.line("auto", WARN, "no CI workflow — `/flow-auto` needs green CI to merge; run `flow ci init` (controlled mode is unaffected)")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_doctor.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/flow_aidlc/commands/doctor.py tests/test_doctor.py
git commit -m "feat(modes): flow doctor auto-readiness line (CI backstop check)"
```

---

## Task 4: `/flow-auto` command + `steps/auto/loop.md`

**Files:**
- Create: `src/flow_aidlc/engine/claude/commands/flow-auto.md`
- Create: `src/flow_aidlc/engine/flow/steps/auto/loop.md`
- Test: `tests/test_execution_modes.py` (new)

**Interfaces:**
- Produces: the `/flow-auto` command surface and the outer-loop guide the command loads.

- [ ] **Step 1: Write the failing structural test**

```python
# tests/test_execution_modes.py  (new file)
from flow_aidlc.engine_assets import engine_dir


def _engine():
    return engine_dir()


def test_flow_auto_command_exists_and_loads_loop():
    cmd = (_engine() / "claude" / "commands" / "flow-auto.md").read_text()
    assert "steps/auto/loop.md" in cmd
    # The command must state the two hard preconditions.
    assert "flow ci init" in cmd or "CI" in cmd
    assert "flow-auto" in cmd


def test_auto_loop_guide_covers_pull_park_merge_report():
    loop = (_engine() / "flow" / "steps" / "auto" / "loop.md").read_text()
    for marker in ("flow-auto", ".flow/STOP", "max_tasks", "flow-blocked", "green"):
        assert marker in loop, marker
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_execution_modes.py -q`
Expected: FAIL with `FileNotFoundError` (files don't exist yet).

- [ ] **Step 3: Author `flow-auto.md`**

Create `src/flow_aidlc/engine/claude/commands/flow-auto.md`:

```markdown
---
description: Run Flow in auto mode — grind the flow-auto-labeled backlog autonomously (no checkpoints; adversarial panels gate each stage; merge on green CI). Terminal only when the queue is empty, a cap is hit, or .flow/STOP appears.
---

Read `.flow/playbook.md` (the "Execution modes" section) and load `.flow/steps/auto/loop.md`, then run the autonomous loop.

**Preconditions (refuse if unmet):**
1. A CI workflow exists (`flow ci init`) — green CI is the auto-merge backstop. If absent, STOP and tell the user to run `flow ci init`.
2. `config.yaml → tracker` is configured with write scope (the loop pulls + comments on tickets).
If either fails, do not start; report what's missing.

**Invocation:**
- `/flow-auto` — grind every open ticket carrying the `execution.label` (default `flow-auto`) in priority order.
- `/flow-auto <id>` — run exactly one ticket autonomously.

**Non-negotiable:** auto mode runs every gate controlled mode runs; it only removes the human `/flow-approve` stops and adds the adversarial panels + merge-on-green-CI. Check `.flow/STOP` before each task and each stage — if present, stop gracefully after the current unit.
```

- [ ] **Step 4: Author `steps/auto/loop.md`**

Create `src/flow_aidlc/engine/flow/steps/auto/loop.md` with these required sections (author the prose; the structural test enforces the markers):

```markdown
# Auto mode — the autonomous loop

Drives one or many tickets through Scope→Shape→Build→Ship with NO human
checkpoints. Load per `/flow-auto`.

## Preconditions
- CI workflow present (green CI is the merge backstop) and tracker write scope.
- Read `config.yaml → execution` for: `label` (default flow-auto), `max_tasks`
  (default 5), `budget`, `review.max_rounds`, `merge.{gate,target}`.

## The loop
1. **Kill-switch check:** if `.flow/STOP` exists, stop — report and exit.
2. **Pull next task:** via the tracker adapter (`steps/shared/tracker.md`
   `DEDUP_SEARCH`/`GET_TICKET`), the highest-priority open ticket labeled
   `<execution.label>` (or the `<id>` argument). None → exit (queue empty).
3. **Run the playbook without stops:** execute Scope→Shape→Build→Ship. At every
   `checkpoint: yes` stage, run the stage-typed adversarial panel
   (`steps/auto/panel-review.md`) instead of stopping for `/flow-approve`.
4. **Ship + merge:** follow `steps/ship/open-pr.md` then `steps/auto/merge.md`
   (open the PR, poll checks, merge only on green CI).
5. **On success:** the ticket auto-closes via `Fixes #`; increment the merged
   count; go to 1.
6. **On a task that cannot settle** (panel non-converge at `review.max_rounds`,
   or CI red after fixes): PARK it — leave a draft PR, add the `flow-blocked`
   label + a comment on why, and continue to the next task (do not halt the run).
7. **Stop conditions:** queue empty | merged count == `max_tasks` | budget
   exhausted | `.flow/STOP` present. Then emit `steps/auto/report.md`.

## Guarantees
- Every gate that controlled mode runs still runs here.
- One stuck task never halts the run — it is parked and reported.
```

- [ ] **Step 5: Regenerate the plugin and run tests**

Run:
```bash
uv run --with pyyaml flow plugin build
uv run --with pytest --with pyyaml python -m pytest tests/test_execution_modes.py tests/test_no_dangling_adr_refs.py -q
```
Expected: PASS. (`flow plugin build` mirrors the new command into `plugin/commands/`.)

- [ ] **Step 6: Commit**

```bash
git add src/flow_aidlc/engine/claude/commands/flow-auto.md src/flow_aidlc/engine/flow/steps/auto/loop.md plugin/ tests/test_execution_modes.py
git commit -m "feat(modes): /flow-auto command + autonomous loop guide"
```

---

## Task 5: Playbook "Execution modes" + stage-typed panels

**Files:**
- Modify: `src/flow_aidlc/engine/flow/playbook.md`
- Create: `src/flow_aidlc/engine/flow/steps/auto/panel-review.md`
- Modify: `src/flow_aidlc/engine/flow/steps/build/verify.md`, `src/flow_aidlc/engine/flow/steps/ship/branch-hardening.md`
- Test: `tests/test_execution_modes.py`

**Interfaces:**
- Consumes: `config.review.branch_hardening` (existing pr-review-toolkit list).
- Produces: the "Execution modes" playbook section + the panel-review guide referenced by `loop.md`.

- [ ] **Step 1: Write the failing structural tests**

```python
# add to tests/test_execution_modes.py
def test_playbook_has_execution_modes_section():
    pb = (_engine() / "flow" / "playbook.md").read_text()
    assert "## Execution modes" in pb
    assert "controlled" in pb and "auto" in pb
    # In auto, the human stop is replaced by the panel — both ideas present.
    assert "/flow-approve" in pb and "panel" in pb.lower()


def test_panel_review_guide_is_stage_typed_and_reuses_pr_review_toolkit():
    pr = (_engine() / "flow" / "steps" / "auto" / "panel-review.md").read_text()
    assert "pr-review-toolkit" in pr           # code gates reuse it
    assert "guardrail-verifier" in pr
    assert "checkpoint-reviewer" in pr          # prose gates
    for marker in ("high-severity", "max_rounds", "park"):
        assert marker in pr, marker
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_execution_modes.py -k "execution_modes_section or panel_review" -q`
Expected: FAIL.

- [ ] **Step 3: Add the "Execution modes" section to `playbook.md`**

Insert after the "Checkpoint Rule" section:

```markdown
## Execution modes

Flow runs in one of two modes:

- **controlled (default):** at each `checkpoint: yes` stage, STOP and wait for
  `/flow-approve` (the `checkpoint-stop` hook reminds you). Terminates at open-PR.
  This is the behavior described throughout this playbook unless auto mode is active.
- **auto (`/flow-auto` only):** NO human stops. At each `checkpoint: yes` stage,
  run the stage-typed **adversarial reviewer panel** (`steps/auto/panel-review.md`)
  in place of `/flow-approve`; on consensus, advance automatically; on
  non-convergence at `execution.review.max_rounds`, park the task. Ship opens AND
  merges the PR on green CI (`steps/auto/merge.md`), then the loop
  (`steps/auto/loop.md`) pulls the next `execution.label` ticket. Auto runs EVERY
  gate controlled runs — it only removes the human stop and adds panel review +
  merge. Auto is entered only via `/flow-auto`; there is no config toggle.
```

- [ ] **Step 4: Author `steps/auto/panel-review.md`**

Create `src/flow_aidlc/engine/flow/steps/auto/panel-review.md`:

```markdown
# Auto mode — stage-typed adversarial panel review

Replaces the human `/flow-approve` at a `checkpoint: yes` stage. Dispatch a panel
matched to the stage's artifact, require consensus, fix-loop until clean or park.

## Consensus
Consensus = every panel member clears with NO open high-severity finding. Any
high-severity finding fails the gate. Findings below high-severity are recorded
and carried to the final report — not looped on.

## Fix loop
On a failed gate: the stage's own agent revises to address the findings, then the
panel re-reviews the change only. Repeat up to `config.execution.review.max_rounds`
(default 5). Converge → advance (no human). Cap without convergence → PARK the task
(`steps/auto/loop.md` step 6).

## Stage-typed panels
| Gate | Artifact | Panel |
|---|---|---|
| Scope/publish, Shape/requirements, Shape/design | prose | `checkpoint-reviewer` + critics (completeness, traceability, ambiguity), `execution.review.panel_size` total |
| Build/code-plan | plan | `checkpoint-reviewer` + a plan critic |
| Build/verify | slice diff | `guardrail-verifier` + a `pr-review-toolkit` subset (`code-reviewer`, `silent-failure-hunter`, `pr-test-analyzer`, `type-design-analyzer`) |
| Ship/branch-hardening | branch diff | the full `config.review.branch_hardening` set + `guardrail-verifier` |

The code-gate panels ARE `config.review.branch_hardening` (a subset per slice at
Build/verify) — no new review agents.
```

- [ ] **Step 5: Add auto-mode pointers to the code-gate step guides**

Append to `steps/build/verify.md` (end of the file) a short subsection:

```markdown
## Auto mode

In auto mode (`/flow-auto`) this checkpoint is gated by the stage-typed panel in
`steps/auto/panel-review.md` (guardrail-verifier + the pr-review-toolkit subset on
the slice diff) instead of `/flow-approve`. Same gate, no human stop.
```

Append to `steps/ship/branch-hardening.md` (end of the file) a short subsection:

```markdown
## Auto mode

In auto mode this checkpoint is gated by the full `config.review.branch_hardening`
panel + guardrail-verifier via `steps/auto/panel-review.md` (no `/flow-approve`);
on consensus the run proceeds to `steps/auto/merge.md`.
```

- [ ] **Step 6: Run tests + lint**

Run:
```bash
uv run --with pytest --with pyyaml python -m pytest tests/test_execution_modes.py tests/test_no_dangling_adr_refs.py -q
```
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/flow_aidlc/engine/flow/playbook.md src/flow_aidlc/engine/flow/steps/auto/panel-review.md src/flow_aidlc/engine/flow/steps/build/verify.md src/flow_aidlc/engine/flow/steps/ship/branch-hardening.md tests/test_execution_modes.py
git commit -m "feat(modes): playbook Execution modes + stage-typed panels (reuse pr-review-toolkit)"
```

---

## Task 6: Ship poll-and-merge + report + checkpoint-stop bypass

**Files:**
- Create: `src/flow_aidlc/engine/flow/steps/auto/merge.md`, `src/flow_aidlc/engine/flow/steps/auto/report.md`
- Modify: `src/flow_aidlc/engine/flow/steps/ship/open-pr.md`, `src/flow_aidlc/engine/claude/hooks/checkpoint-stop.sh`
- Test: `tests/test_execution_modes.py`

**Interfaces:**
- Consumes: the tracker/VCS adapter (`OPEN_PR`, check-polling), `config.execution.merge`.
- Produces: the auto merge + report guides; the hook no-ops in auto.

- [ ] **Step 1: Write the failing structural tests**

```python
# add to tests/test_execution_modes.py
def test_merge_guide_polls_ci_and_merges_on_green():
    m = (_engine() / "flow" / "steps" / "auto" / "merge.md").read_text()
    for marker in ("green", "poll", "branch protection", "flow-blocked"):
        assert marker in m.lower() or marker in m, marker


def test_report_guide_lists_merged_and_parked():
    r = (_engine() / "flow" / "steps" / "auto" / "report.md").read_text()
    assert "merged" in r.lower() and "parked" in r.lower()


def test_checkpoint_stop_hook_bypasses_in_auto():
    h = (_engine() / "claude" / "hooks" / "checkpoint-stop.sh").read_text()
    assert "STOP" in h  # the .flow/STOP sentinel or FLOW_MODE handling is referenced
    assert "auto" in h.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_execution_modes.py -k "merge_guide or report_guide or checkpoint_stop" -q`
Expected: FAIL.

- [ ] **Step 3: Author `steps/auto/merge.md`**

Create `src/flow_aidlc/engine/flow/steps/auto/merge.md`:

```markdown
# Auto mode — open, poll CI, merge on green

Runs after `steps/ship/open-pr.md` opens the PR (auto mode only). TWO independent
gates must both be green to merge: (a) every in-session adversarial panel cleared,
and (b) the PR's required CI checks green.

1. **Open** the PR via the tracker/VCS adapter `OPEN_PR` (base = `execution.merge.target`
   or `config.vcs.base`), body includes `Fixes <id>`.
2. **Poll** the PR's required checks via the tracker/VCS MCP until they settle.
3. **Green →** merge (respect branch protection; never override it). The ticket
   auto-closes via `Fixes <id>`. Return success to the loop.
4. **Red →** pull the failing check output, run a fix-loop in the workspace, push,
   and re-poll. Bounded by `execution.review.max_rounds`.
5. **Still red / timeout →** do NOT merge. Convert to a draft PR, add the
   `flow-blocked` label + a comment with the failing checks, and return "parked"
   to the loop (`steps/auto/loop.md` step 6).

Branch protection is authoritative — if it blocks the merge, park (never bypass).
```

- [ ] **Step 4: Author `steps/auto/report.md`**

Create `src/flow_aidlc/engine/flow/steps/auto/report.md`:

```markdown
# Auto mode — final report

Emitted when the loop stops (queue empty | max_tasks | budget | .flow/STOP). List:

- **Merged:** ticket id, PR url, one-line summary — one row each.
- **Parked (flow-blocked):** ticket id, draft PR url, the blocking reason.
- **Skipped:** any ticket not reached (cap/kill-switch), so the human knows the tail.

End with the stop reason and the merged/parked counts.
```

- [ ] **Step 5: Add the open-pr auto branch + hook bypass**

Append to `steps/ship/open-pr.md` a short subsection:

```markdown
## Auto mode

In auto mode, open-pr does not terminate the Flow. After opening the PR, continue
to `steps/auto/merge.md` (poll CI, merge on green, else park). The human-owned
merge applies to controlled mode only.
```

Edit `src/flow_aidlc/engine/claude/hooks/checkpoint-stop.sh` — add an early
no-op in auto mode. After `flow_read_input` and before the worklog lookup, insert:

```bash
# Auto mode bypass: /flow-auto runs without human checkpoints. If the repo is in
# an auto run (a .flow/STOP sentinel is the kill-switch, and FLOW_MODE=auto marks
# the session), do not print the checkpoint reminder.
if [ "${FLOW_MODE:-}" = "auto" ]; then
  exit 0
fi
```

(The `.flow/STOP` file remains the kill-switch checked by the loop; the hook only
suppresses the human reminder when `FLOW_MODE=auto`.)

- [ ] **Step 6: Run tests + full suite + plugin regen**

Run:
```bash
uv run --with pyyaml flow plugin build
uv run --with pytest --with pyyaml python -m pytest -q
```
Expected: PASS (full suite green; plugin regenerated).

- [ ] **Step 7: Commit**

```bash
git add src/flow_aidlc/engine/flow/steps/auto/merge.md src/flow_aidlc/engine/flow/steps/auto/report.md src/flow_aidlc/engine/flow/steps/ship/open-pr.md src/flow_aidlc/engine/claude/hooks/checkpoint-stop.sh plugin/ tests/test_execution_modes.py
git commit -m "feat(modes): Ship poll-and-merge + final report + checkpoint-stop auto bypass"
```

---

## Final Verification (after all tasks)

- [ ] Full suite: `uv run --with pytest --with pyyaml python -m pytest -q` → all pass.
- [ ] Live: `flow init` into a temp repo → `flow check` still `gate PASSED` (the `execution:` block is valid); `flow doctor` shows an `auto` line (WARN without CI, PASS after `flow ci init`).
- [ ] `git grep -n "TODO\|TBD" src/flow_aidlc/engine/flow/steps/auto` → empty.
- [ ] Plugin regenerated: `plugin/commands/flow-auto.md` exists.

---

## Self-Review (completed by plan author)

- **Spec coverage:** §5 modes → Task 5 (playbook); §6 control surface + safety → Tasks 1 (config), 4 (`/flow-auto` + preconditions + `.flow/STOP`), 3 (doctor CI precondition); §7 stage-typed panels → Task 5; §8 poll-and-merge + park + outer loop + report → Tasks 4 & 6; §9 config schema → Tasks 1 & 2; §11 implementation surface → matches; §14 acceptance 1–4,6 → Final Verification (5 is Plan 2 / Impeccable). **Impeccable (§10, acceptance 5) is intentionally deferred to Plan 2.**
- **Placeholder scan:** Python tasks carry full code + tests; engine tasks carry the exact asset content + a structural test asserting the required markers. No TBD/TODO.
- **Type consistency:** `_check_auto(rep, root)`, C8 in `check()`, the `execution:` keys (`label/max_tasks/budget/review.{panel_size,max_rounds}/merge.{gate,target}/require_ci`), and the marker strings the structural tests assert are used identically across tasks.
- **Note:** engine-prose tasks are verified structurally (markers) + by the existing gate/lint staying green + plugin regeneration; agent *runtime* behavior (panels, loop) is methodology exercised by a real `/flow-auto` run, not pytest — stated in the spec §12 and honored here.
