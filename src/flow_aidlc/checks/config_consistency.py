"""Config consistency — .flow/config.yaml is the single source of truth.

Guides and agents are prose (markdown); they cannot interpolate config values
at runtime, so authors sometimes bake literals in. Those copies drift. This
check keeps the prose layer honest against config.yaml.

Failure posture: a genuinely absent ``config.yaml`` is skipped (nothing to
enforce), but an **unparseable** config or a **missing PyYAML** is a BLOCKING
error — a drift-guard must never silently pass on a config it could not read
(this matches ``structure_check`` / ``reference_check``). File reads inside a
check surface a blocking error on failure rather than being silently skipped.

Checks:
  C1 (guardrail parity): every name in ``guardrails.always_on`` /
     ``guardrails.optional`` has a matching rule file under
     ``.flow/guardrails/{always-on,optional}/<name>.md`` — and vice versa.
  C2 (no hardcoded repo): the config's ``tracker.repo`` value must not appear
     as a literal in any ``.md`` under ``.flow/`` or ``.claude/``. A file may
     opt out with the marker ``config-consistency: allow-repo-literal`` (for a
     runbook that must show a concrete owner/repo).
  C3 (tracker platform): ``tracker.platform`` must have a non-stub mapping in
     the adapter ``.flow/steps/shared/tracker.md`` (no NOT IMPLEMENTED).
  C5 (review echo): every ``review.branch_hardening`` agent must be mentioned in
     ``.flow/steps/ship/branch-hardening.md``.
  C6 (graph backend): ``graph.backend`` must have a non-stub mapping in the graph
     adapter ``.flow/steps/shared/graph.md`` (no NOT IMPLEMENTED).
  C7 (graph paths): ``graph.root`` and every ``graph.focus`` entry must be an
     existing directory, and ``graph.ignore_file`` (if set) must exist — so the
     single-extract scope the config documents actually resolves on disk.

Note: the numbering skips C4 — a "guardrail echo" check that would require each
``always_on`` name to be repeated in the prose files that hardcode the list. The
engine intentionally **de-hardcodes** those files (the guardrail-verifier,
playbook, and build/verify treat ``config.yaml`` as the sole source of truth and
never name guardrails), so there is no prose echo to keep in sync and C4 does not
apply here.

Usage:
    python -m flow_aidlc.checks.config_consistency            # uses repo root
    python -m flow_aidlc.checks.config_consistency <repo_root>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from flow_aidlc.checks._root import find_repo_root

try:
    import yaml  # pyyaml
except ImportError:
    yaml = None  # type: ignore[assignment]


_ALLOW_REPO_LITERAL = "config-consistency: allow-repo-literal"


def _load_config(repo_root: Path) -> tuple[dict | None, str | None]:
    """Load ``.flow/config.yaml``.

    Returns ``(data, error)``:
      - ``(dict, None)``  — parsed config.
      - ``(None, None)``  — config genuinely absent → caller skips (nothing to enforce).
      - ``(None, error)`` — missing PyYAML / parse error / not a mapping → BLOCKING.
    """
    cfg = repo_root / ".flow" / "config.yaml"
    if not cfg.exists():
        return None, None
    if yaml is None:
        return None, "config-consistency: pyyaml not installed — cannot verify config consistency"
    try:
        data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError, UnicodeDecodeError) as exc:
        return None, f"config-consistency: .flow/config.yaml failed to parse — {exc}"
    if not isinstance(data, dict):
        return None, "config-consistency: .flow/config.yaml did not parse to a mapping"
    return data, None


def _mentions(text: str, token: str) -> bool:
    """True if ``token`` appears in ``text`` on word boundaries (not a loose substring)."""
    return re.search(r"\b" + re.escape(token) + r"\b", text) is not None


def check(repo_root: Path | str) -> list[str]:
    """Return a list of error strings (empty → all clear)."""
    repo_root = Path(repo_root)
    errors: list[str] = []

    def read_text(path: Path) -> str | None:
        """Read a file for a check; surface a blocking error on failure (never silently skip)."""
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(
                f"config-consistency: could not read {path.relative_to(repo_root)} — {exc}"
            )
            return None

    def adapter_implements(value, adapter_rel: str, key: str, code: str) -> None:
        """Assert a config choice has a non-stub '### <value>' mapping in an adapter file."""
        if not value:
            return
        adapter = repo_root / adapter_rel
        if not adapter.exists():
            errors.append(f"{code} {key}: config sets {key}='{value}' but the adapter {adapter_rel} is missing")
            return
        text = read_text(adapter)
        if text is None:
            return
        # End the value on whitespace or end-of-line, not \b — otherwise a value like
        # 'github' would match a '### github-issues' heading (the hyphen is a \b).
        # Bound the section at the next heading of the SAME-OR-SHALLOWER depth (## or
        # ###) — not just the next ###. Otherwise the last ### section bleeds into a
        # following ## section (e.g. '## Rule'), whose prose may mention "NOT
        # IMPLEMENTED" and trip a false positive.
        section = re.search(
            r"^###\s+" + re.escape(value) + r"(?=\s|$)(.*?)(?=^\#{2,3}\s|\Z)", text, re.S | re.M | re.I
        )
        if not section:
            errors.append(f"{code} {key}: no '### {value}' mapping in {adapter_rel} — the adapter does not implement '{value}'")
        elif "NOT IMPLEMENTED" in section.group(1).upper():
            errors.append(f"{code} {key}: '{value}' is a NOT IMPLEMENTED stub in {adapter_rel} — implement its mapping before setting {key}='{value}'")

    cfg, load_error = _load_config(repo_root)
    if load_error:
        return [load_error]        # unparseable / no pyyaml → BLOCK, never fail-open
    if cfg is None:
        return errors              # config genuinely absent → nothing to enforce

    guardrails = cfg.get("guardrails", {}) or {}
    gr_dir = repo_root / ".flow" / "guardrails"

    # ---- C1: guardrail config <-> rule-file parity ----
    for tier_key, subdir in (("always_on", "always-on"), ("optional", "optional")):
        configured = set(guardrails.get(tier_key, []) or [])
        tier_dir = gr_dir / subdir
        on_disk: set[str] = set()
        if tier_dir.is_dir():
            for f in tier_dir.glob("*.md"):
                if f.name.endswith(".ask.md"):
                    continue  # opt-in prompt stubs, not rule specs
                if f.name in ("README.md", "TEMPLATE.md"):
                    continue  # engine authoring aids, not project rule specs
                on_disk.add(f.stem)
        for name in sorted(configured - on_disk):
            errors.append(
                f"C1 guardrail parity: config lists '{name}' in guardrails.{tier_key} "
                f"but .flow/guardrails/{subdir}/{name}.md is missing"
            )
        for name in sorted(on_disk - configured):
            errors.append(
                f"C1 guardrail parity: .flow/guardrails/{subdir}/{name}.md exists "
                f"but '{name}' is not in config guardrails.{tier_key}"
            )

    # ---- C2: tracker.repo must not be hardcoded in any .md ----
    repo = (cfg.get("tracker", {}) or {}).get("repo")
    if repo:
        for base in (".flow", ".claude"):
            base_dir = repo_root / base
            if not base_dir.is_dir():
                continue
            for f in sorted(base_dir.rglob("*.md")):
                text = read_text(f)
                if text is None:
                    continue
                if _ALLOW_REPO_LITERAL in text:
                    continue  # explicit opt-out (e.g. a runbook that must show owner/repo)
                if repo in text:
                    errors.append(
                        f"C2 hardcoded repo: '{repo}' is hardcoded in "
                        f"{f.relative_to(repo_root)} — reference `config.yaml → tracker.repo` "
                        f"instead (or add a '{_ALLOW_REPO_LITERAL}' marker if intentional)"
                    )

    # ---- C3: configured tracker.platform must be implemented in the tracker adapter ----
    adapter_implements(
        (cfg.get("tracker", {}) or {}).get("platform"),
        ".flow/steps/shared/tracker.md", "tracker.platform", "C3",
    )

    # ---- C5: branch-hardening review set must be echoed in the step guide ----
    review = cfg.get("review", {}) or {}
    hardening = list(review.get("branch_hardening", []) or [])
    if hardening:
        guide = repo_root / ".flow" / "steps" / "ship" / "branch-hardening.md"
        if guide.exists():
            text = read_text(guide)
            if text is not None:
                for agent in hardening:
                    if not _mentions(text, agent):
                        errors.append(
                            f"C5 review echo: '{agent}' is in config review.branch_hardening "
                            f"but not mentioned in .flow/steps/ship/branch-hardening.md"
                        )

    # ---- C6: configured graph.backend must be implemented in the graph adapter ----
    adapter_implements(
        (cfg.get("graph", {}) or {}).get("backend"),
        ".flow/steps/shared/graph.md", "graph.backend", "C6",
    )

    # ---- C7: graph.root + graph.focus dirs must exist; graph.ignore_file must exist ----
    graph = cfg.get("graph", {}) or {}
    root = graph.get("root")
    if root and not (repo_root / root).is_dir():
        errors.append(
            f"C7 graph.root: config sets graph.root '{root}' but that directory does not exist"
        )
    for path in (graph.get("focus") or []):
        if not (repo_root / path).is_dir():
            errors.append(
                f"C7 graph.focus: config lists graph.focus '{path}' but that directory does not exist"
            )
    ignore_file = graph.get("ignore_file")
    if ignore_file and not (repo_root / ignore_file).exists():
        errors.append(
            f"C7 graph.ignore_file: config sets graph.ignore_file '{ignore_file}' but it does not exist"
        )

    return errors


def main(argv: list[str] | None = None) -> int:
    args = (argv or sys.argv)[1:]
    repo_root = Path(args[0]) if args else find_repo_root()
    errors = check(repo_root)
    if errors:
        print("config-consistency FAILED:")
        for e in errors:
            print(f"  {e}")
        return 1
    print("config-consistency OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
