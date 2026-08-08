# Impeccable Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire Impeccable (Apache-2.0 design-quality Claude Code skill pack) into Flow for **validation + UI generation**, grounded in `PRODUCT.md`/`DESIGN.md` — as an opt-in `flow setup` auto-install, a CI gate, a `flow doctor` detection, and Build/auto touchpoints.

**Architecture:** Thin CLI/config (a `flow ci init --gates impeccable` step, a `flow setup --with-impeccable` install+guide, a `flow doctor` opt-in detection) + engine prose touchpoints (Build generate/verify + the auto-mode UI panel + knowledge-map reference to the standards + docs). Impeccable installs project-local via a non-interactive CLI, so `flow setup` can drive it — unlike the marketplace skill packs.

**Tech Stack:** Python 3.10+ (stdlib), pytest (dev); Impeccable via `npx` (Node); engine assets are Markdown consumed by Claude Code.

## Global Constraints

- Python `>=3.10`; new code uses `from __future__ import annotations` where a module needs it.
- Stdlib only for new runtime code (no new Python deps).
- **Scope: validation + UI generation + the `PRODUCT.md`/`DESIGN.md` standards only.** NOT Impeccable's `live` mode or `worlds`/dice.
- Impeccable is **opt-in** — never installed by a plain `flow init`/`flow setup`; only via `flow setup --with-impeccable`. It is never a hard prerequisite and never a FAIL in `flow doctor`.
- The installer is non-interactive + project-local: `npx impeccable install --providers=claude --scope=project`. It writes `.claude/skills/impeccable/`.
- `PRODUCT.md`/`DESIGN.md` are **tracked** (committed); only Impeccable's **ephemera** are gitignored (`.impeccable/*.png`, `.impeccable/sessions/`, `.impeccable/previews/`, `.impeccable/cache/`, `.impeccable/config.local.json`).
- **`flow setup` cannot run `/impeccable init`** (a Claude Code slash command, not a CLI). Setup installs the skill + prints guidance to run `/impeccable init` in Claude Code to author the standards. Setup does NOT create `PRODUCT.md`/`DESIGN.md` itself.
- `flow setup`'s posture is **detect + guide + keep going** — a missing `npx` is reported, not fatal.
- Tests run via `uv run --with pytest --with pyyaml python -m pytest -q` when pytest isn't on PATH.
- Engine markdown must not introduce dangling ADR refs (`decisions/NNNN` / `ADR NNNN`).
- Reference spec: `docs/superpowers/specs/2026-08-08-flow-execution-modes-design.md` §10.

---

## File Structure

- **`src/flow_aidlc/commands/ci.py`** — add `impeccable` to `_GATES` + the gate-step dicts. (Task 1)
- **`src/flow_aidlc/commands/setup.py`** — add `--with-impeccable` (install + gitignore ephemera + guide). (Task 2)
- **`src/flow_aidlc/commands/doctor.py`** — add `_check_impeccable` (opt-in detection). (Task 3)
- **Engine prose:** `steps/build/generate.md`, `steps/build/verify.md`, `steps/auto/panel-review.md`, `knowledge-map.tmpl.yaml`, `INTEGRATIONS.md`, `README.md`. (Task 4)
- **Tests:** `tests/test_ci.py`, `tests/test_setup.py`, `tests/test_doctor.py`, `tests/test_impeccable.py` (new, structural).

---

## Task 1: `flow ci init --gates impeccable`

**Files:**
- Modify: `src/flow_aidlc/commands/ci.py`
- Test: `tests/test_ci.py`

**Interfaces:**
- Consumes: the existing `_GATES` tuple + `_GH_GATE_STEPS`/`_GL_GATE_STEPS` dicts (currently `semgrep`, `conftest`).
- Produces: `impeccable` as a third supported gate emitting an `npx impeccable detect --json .` step.

- [ ] **Step 1: Write the failing tests**

```python
# add to tests/test_ci.py
def test_gates_impeccable_step(tmp_path):
    _flow_repo(tmp_path)
    ci.run(["init", "--gates", "impeccable", "--path", str(tmp_path)])
    text = (tmp_path / ".github" / "workflows" / "flow-check.yml").read_text()
    assert "impeccable detect" in text

def test_gates_impeccable_gitlab(tmp_path):
    _flow_repo(tmp_path)
    ci.run(["init", "--provider", "gitlab", "--gates", "impeccable", "--path", str(tmp_path)])
    assert "impeccable detect" in (tmp_path / ".gitlab-ci.yml").read_text()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_ci.py -k impeccable -q`
Expected: FAIL — `impeccable` is an unknown gate (exit 2), no step emitted.

- [ ] **Step 3: Add the gate**

In `src/flow_aidlc/commands/ci.py`:

Change `_GATES`:
```python
_GATES = ("semgrep", "conftest", "impeccable")
```

Add to `_GH_GATE_STEPS` (inside the dict literal):
```python
    "impeccable": (
        "      - name: Impeccable design quality\n"
        "        run: npx --yes impeccable detect --json .\n"
    ),
```

Add to `_GL_GATE_STEPS`:
```python
    "impeccable": "    - npx --yes impeccable detect --json .\n",
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_ci.py -q`
Expected: PASS (existing gate tests + the 2 new).

- [ ] **Step 5: Commit**

```bash
git add src/flow_aidlc/commands/ci.py tests/test_ci.py
git commit -m "feat(impeccable): flow ci init --gates impeccable (design-quality CI gate)"
```

---

## Task 2: `flow setup --with-impeccable`

**Files:**
- Modify: `src/flow_aidlc/commands/setup.py`
- Test: `tests/test_setup.py`

**Interfaces:**
- Consumes: the existing `run(argv)`, `_run(cmd, cwd)`, `step(msg)`, `shutil.which`, and the `_build_parser()` argparse setup.
- Produces: a `--with-impeccable` flag; when set, an install step (`npx impeccable install --providers=claude --scope=project`, detect-and-guide), gitignore of the ephemera, and printed guidance to run `/impeccable init` in Claude Code.

- [ ] **Step 1: Write the failing tests**

```python
# add to tests/test_setup.py
def test_with_impeccable_dry_run_prints_install(tmp_path, capsys):
    _git_init(tmp_path)
    from flow_aidlc.commands import init, setup
    init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)])
    rc = setup.run(["--with-impeccable", "--dry-run", "--path", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "impeccable install" in out
    assert "/impeccable init" in out   # guidance for the standards (slash command)

def test_without_flag_no_impeccable(tmp_path, capsys):
    _git_init(tmp_path)
    from flow_aidlc.commands import init, setup
    init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)])
    setup.run(["--dry-run", "--path", str(tmp_path)])
    assert "impeccable" not in capsys.readouterr().out.lower()

def test_with_impeccable_gitignores_ephemera(tmp_path):
    _git_init(tmp_path)
    from flow_aidlc.commands import init, setup
    init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)])
    setup.run(["--with-impeccable", "--path", str(tmp_path)])   # not dry-run: writes gitignore
    gi = (tmp_path / ".gitignore").read_text()
    assert ".impeccable/cache/" in gi
```

(`_git_init` already exists in `tests/test_setup.py`.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_setup.py -k impeccable -q`
Expected: FAIL — no `--with-impeccable` flag.

- [ ] **Step 3: Implement the flag**

In `src/flow_aidlc/commands/setup.py`:

(a) Add to `_build_parser()`:
```python
    p.add_argument("--with-impeccable", action="store_true",
                   help="Also install the Impeccable design-quality skill (opt-in; UI projects).")
```

(b) Add a module-level constant near `_GRAPHIFY_SPEC`:
```python
_IMPECCABLE_EPHEMERA = (
    ".impeccable/*.png", ".impeccable/sessions/", ".impeccable/previews/",
    ".impeccable/cache/", ".impeccable/config.local.json",
)
```

(c) In `run()`, after the doctor step (step 3) and before the final print, add the impeccable step:
```python
    # ---- 4. Impeccable (opt-in) ------------------------------------------
    if args.with_impeccable:
        step("install Impeccable (design quality): npx impeccable install --providers=claude --scope=project")
        if not dry:
            if shutil.which("npx"):
                rc = _run(["npx", "--yes", "impeccable", "install", "--providers=claude", "--scope=project"], root)
                if rc != 0:
                    print(f"  [WARN] impeccable install exited {rc} — continuing.")
            else:
                print("  [WARN] `npx` not found — skipping Impeccable install.")
                print("         Install Node, then: npx impeccable install --providers=claude --scope=project")
            _ensure_impeccable_gitignore(root)
        print("  Author the standards in Claude Code: run `/impeccable init` to create PRODUCT.md + DESIGN.md")
        print("  (they are committed; Flow reads them for grounding — see INTEGRATIONS.md)")
```

(d) Add the helper (near the other module functions):
```python
def _ensure_impeccable_gitignore(root: Path) -> None:
    """Append Impeccable ephemera to .gitignore (PRODUCT.md/DESIGN.md stay tracked)."""
    path = root / ".gitignore"
    existing = set()
    text = ""
    if path.exists():
        text = path.read_text(encoding="utf-8")
        existing = {ln.strip() for ln in text.splitlines()}
    missing = [e for e in _IMPECCABLE_EPHEMERA if e not in existing]
    if not missing:
        return
    prefix = "" if (not text or text.endswith("\n")) else "\n"
    path.write_text(text + prefix + "\n".join(missing) + "\n", encoding="utf-8")
```

Ensure `from pathlib import Path` and `import shutil` are imported (shutil is already used; add if missing).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_setup.py -q`
Expected: PASS (existing setup tests + the 3 new).

- [ ] **Step 5: Commit**

```bash
git add src/flow_aidlc/commands/setup.py tests/test_setup.py
git commit -m "feat(impeccable): flow setup --with-impeccable (install + ephemera + guide)"
```

---

## Task 3: `flow doctor` Impeccable detection

**Files:**
- Modify: `src/flow_aidlc/commands/doctor.py`
- Test: `tests/test_doctor.py`

**Interfaces:**
- Consumes: `_Report` (`.line`, `.any_fail`), `PASS`/`WARN`.
- Produces: `_check_impeccable(rep, root) -> None` — reports an `impeccable` line ONLY when the repo has opted in (the skill dir OR a standards file exists). Silent otherwise (never nags a non-UI repo). WARN/PASS only.

- [ ] **Step 1: Write the failing tests**

```python
# add to tests/test_doctor.py
def test_check_impeccable_silent_when_absent(tmp_path, capsys):
    rep = doctor._Report()
    doctor._check_impeccable(rep, tmp_path)
    assert "impeccable" not in capsys.readouterr().out.lower()  # no opt-in signal → no line
    assert rep.any_fail is False

def test_check_impeccable_pass_when_skill_and_standard(tmp_path, capsys):
    (tmp_path / ".claude" / "skills" / "impeccable").mkdir(parents=True)
    (tmp_path / "PRODUCT.md").write_text("# Product\n")
    rep = doctor._Report()
    doctor._check_impeccable(rep, tmp_path)
    assert "[PASS]" in capsys.readouterr().out
    assert rep.any_fail is False

def test_check_impeccable_warns_when_partial(tmp_path, capsys):
    # standards present but the skill isn't installed → WARN (opted in, but incomplete)
    (tmp_path / "DESIGN.md").write_text("# Design\n")
    rep = doctor._Report()
    doctor._check_impeccable(rep, tmp_path)
    out = capsys.readouterr().out
    assert "[WARN]" in out and "impeccable" in out
    assert rep.any_fail is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_doctor.py -k impeccable -q`
Expected: FAIL with `AttributeError: _check_impeccable`.

- [ ] **Step 3: Implement the check**

In `src/flow_aidlc/commands/doctor.py`, add the call in `run()` after `_check_auto(rep, root)`:
```python
    _check_impeccable(rep, root)
```

Add the function (near `_check_auto`):
```python
def _check_impeccable(rep: _Report, root: Path) -> None:
    """Optional design-quality check (Impeccable). Only reports when the repo has
    opted in — i.e. the skill is installed OR a PRODUCT.md/DESIGN.md exists. Stays
    SILENT otherwise so a non-UI repo is never nagged. WARN/PASS only, never FAIL.
    """
    skill = (root / ".claude" / "skills" / "impeccable").is_dir()
    standards = [n for n in ("PRODUCT.md", "DESIGN.md") if (root / n).exists()]
    if not skill and not standards:
        return  # not opted in — say nothing
    if skill and standards:
        rep.line("impeccable", PASS, f"skill installed; standards: {', '.join(standards)}")
    elif skill and not standards:
        rep.line("impeccable", WARN, "skill installed but no PRODUCT.md/DESIGN.md — run `/impeccable init`")
    else:
        rep.line("impeccable", WARN, "PRODUCT.md/DESIGN.md present but skill missing — `flow setup --with-impeccable`")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_doctor.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/flow_aidlc/commands/doctor.py tests/test_doctor.py
git commit -m "feat(impeccable): flow doctor opt-in Impeccable detection (silent unless adopted)"
```

---

## Task 4: Engine prose touchpoints + docs

**Files:**
- Modify: `src/flow_aidlc/engine/flow/steps/build/generate.md`, `src/flow_aidlc/engine/flow/steps/build/verify.md`, `src/flow_aidlc/engine/flow/steps/auto/panel-review.md`, `src/flow_aidlc/engine/flow/knowledge-map.tmpl.yaml`, `src/flow_aidlc/engine/flow/INTEGRATIONS.md`, `README.md`
- Test: `tests/test_impeccable.py` (new, structural)

**Interfaces:**
- Produces: the engine-prose touchpoints that tell the Build/auto agents when + how to use Impeccable, grounded in `PRODUCT.md`/`DESIGN.md`.

- [ ] **Step 1: Write the failing structural tests**

```python
# tests/test_impeccable.py  (new)
from flow_aidlc.engine_assets import engine_dir


def _e():
    return engine_dir()


def test_generate_guide_mentions_impeccable_ui():
    t = (_e() / "flow" / "steps" / "build" / "generate.md").read_text()
    assert "impeccable" in t.lower() and "DESIGN.md" in t


def test_verify_guide_mentions_impeccable_validation():
    t = (_e() / "flow" / "steps" / "build" / "verify.md").read_text()
    assert "impeccable" in t.lower()


def test_panel_review_adds_impeccable_ui_lens():
    t = (_e() / "flow" / "steps" / "auto" / "panel-review.md").read_text()
    assert "impeccable" in t.lower() and "UI" in t


def test_knowledge_map_references_standards():
    t = (_e() / "flow" / "knowledge-map.tmpl.yaml").read_text()
    assert "PRODUCT.md" in t and "DESIGN.md" in t
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest --with pyyaml python -m pytest tests/test_impeccable.py -q`
Expected: FAIL (markers absent).

- [ ] **Step 3: Add the Build/generate touchpoint**

Append to `src/flow_aidlc/engine/flow/steps/build/generate.md`:

```markdown
## Design quality (UI slices — optional, Impeccable)

If the slice produces UI and the Impeccable skill is installed (`flow setup
--with-impeccable`), generate/refine it **against `DESIGN.md`** using the
generation commands (`/impeccable craft|polish|distill|typeset|layout|colorize`)
so the output reflects the product's design language rather than generic defaults.
Non-UI slices ignore this.
```

- [ ] **Step 4: Add the Build/verify touchpoint**

Append to `src/flow_aidlc/engine/flow/steps/build/verify.md`:

```markdown
## Design quality (UI slices — optional, Impeccable)

For a UI slice with Impeccable installed, validate the design against the
standards: `/impeccable audit` (a11y/perf/responsive) + `/impeccable critique`
(UX vs `PRODUCT.md`/`DESIGN.md`), or the deterministic `npx impeccable detect
--json .`. Treat a high-severity design finding like any other verify finding.
```

- [ ] **Step 5: Add Impeccable as the UI panel lens**

In `src/flow_aidlc/engine/flow/steps/auto/panel-review.md`, in the stage-typed
panel table, extend the Build/verify and Ship/branch-hardening rows so a **UI
slice** adds Impeccable. Append this note under the table:

```markdown
**UI slices:** for a diff that changes UI, add **Impeccable** to the Build/verify
and branch-hardening panels as the design-quality lens (`/impeccable audit` +
`critique`, checked against `PRODUCT.md`/`DESIGN.md`) — only when the skill is
installed. It complements the pr-review-toolkit code lenses; it does not replace them.
```

- [ ] **Step 6: Reference the standards in the knowledge map**

In `src/flow_aidlc/engine/flow/knowledge-map.tmpl.yaml`, add a comment/entry so
Scope/Shape read the design standards for grounding. Append at the end:

```yaml
# Design standards (optional, Impeccable): if present, Scope/Shape read these for
# grounding so intent + design reflect the product's design language.
design_standards:
  - PRODUCT.md   # audience, brand, voice, anti-references
  - DESIGN.md    # the design system / standards
```

- [ ] **Step 7: Add the INTEGRATIONS + README docs**

Append to `src/flow_aidlc/engine/flow/INTEGRATIONS.md` under "Optional integrations":

```markdown
### Design quality — Impeccable

[Impeccable](https://impeccable.style/) (Apache-2.0) is a Claude Code skill pack
for UI design quality. Unlike the other skill packs it installs project-local via
a non-interactive CLI, so `flow setup --with-impeccable` installs it
(`npx impeccable install --providers=claude --scope=project`) and gitignores its
ephemera. Author `PRODUCT.md` (audience/voice/anti-references) + `DESIGN.md` (design
system) once via `/impeccable init` in Claude Code — they are committed, and Flow
reads them for grounding at Scope/Shape. Then Build/generate produces UI against
`DESIGN.md`, Build/verify validates via `/impeccable audit` + `critique`, and
`flow ci init --gates impeccable` adds a deterministic `npx impeccable detect
--json .` CI gate. `flow doctor` reports an `impeccable` line once you've adopted it.
```

Add to `README.md` under "What you get" (after the observability bullet):

```markdown
- **Design quality (optional, UI)** — `flow setup --with-impeccable` installs [Impeccable](https://impeccable.style/) (Apache-2.0); Flow reads its `PRODUCT.md`/`DESIGN.md` for grounding, generates/validates UI against them, and `flow ci init --gates impeccable` gates design quality in CI.
```

- [ ] **Step 8: Run tests + guards**

Run:
```bash
uv run --with pytest --with pyyaml python -m pytest tests/test_impeccable.py tests/test_no_dangling_adr_refs.py tests/test_config_consistency.py -q
```
Expected: PASS (config-consistency stays green — the docs add no `tracker.repo` literal; the dangling-ADR guard passes).

- [ ] **Step 9: Commit**

```bash
git add src/flow_aidlc/engine/flow/steps/build/generate.md src/flow_aidlc/engine/flow/steps/build/verify.md src/flow_aidlc/engine/flow/steps/auto/panel-review.md src/flow_aidlc/engine/flow/knowledge-map.tmpl.yaml src/flow_aidlc/engine/flow/INTEGRATIONS.md README.md tests/test_impeccable.py
git commit -m "feat(impeccable): Build/auto touchpoints + knowledge-map standards + docs"
```

---

## Final Verification (after all tasks)

- [ ] Full suite: `uv run --with pytest --with pyyaml python -m pytest -q` → all pass.
- [ ] Live: `flow init` into a temp repo → `flow ci init --gates impeccable` emits the detect step; `flow setup --with-impeccable --dry-run` prints the install + the `/impeccable init` guidance; `flow doctor` stays silent about impeccable (no opt-in signal) on that repo.
- [ ] `git grep -n "TODO\|TBD" src/flow_aidlc/engine/flow/steps/build src/flow_aidlc/engine/flow/steps/auto/panel-review.md` → empty.
- [ ] No plugin regen needed (no `engine/claude/` change) — confirm `git diff --name-only <base>..HEAD | grep engine/claude` is empty.

---

## Self-Review (completed by plan author)

- **Spec coverage (§10):** setup opt-in auto-install → Task 2; PRODUCT/DESIGN standards (authored via `/impeccable init`, referenced by knowledge-map, tracked) → Tasks 2 (guide) & 4 (knowledge-map); Scope/Shape grounding → Task 4 (knowledge-map); Build/generate → Task 4; Build/verify + auto panel → Tasks 4; CI gate → Task 1; doctor detection → Task 3; INTEGRATIONS/README → Task 4. `live`/`worlds` excluded throughout.
- **Spec correction applied:** setup CANNOT run the `/impeccable init` slash command → it installs + guides; standards authoring is a guided in-Claude-Code step. Stated in Global Constraints + Task 2.
- **Placeholder scan:** Python tasks carry full code + tests; the prose task carries the exact appended content + structural marker tests. No TBD/TODO.
- **Type consistency:** `_check_impeccable(rep, root)`, `_ensure_impeccable_gitignore(root)`, `_IMPECCABLE_EPHEMERA`, the `impeccable` gate key, and the marker strings the structural tests assert are used identically across tasks.
- **Note:** the doctor check is deliberately silent unless opted-in (skill dir or a standards file present) so non-UI repos are never nagged — a design decision beyond the spec's "WARN-only," made explicit here.
