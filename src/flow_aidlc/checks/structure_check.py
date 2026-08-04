"""Validate .flow/ methodology structure.

Checks:
1. config.yaml exists and is valid YAML.
2. Each guardrail name in config.yaml has a matching .md file in guardrails/.
3. Each `load:` path referenced in playbook.md (backtick-quoted, starts with
   'steps/') resolves to an existing file under the .flow dir.

Usage:
    python -m flow_aidlc.checks.structure_check              # uses repo's .flow/
    python -m flow_aidlc.checks.structure_check <flow_dir>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from flow_aidlc.checks._root import find_repo_root

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


_LOAD_REF_RE = re.compile(r"`(steps/[^`]+\.md)`")


def check(flow_dir: Path | str) -> list[str]:
    """Return a list of error strings (empty → all clear)."""
    flow_dir = Path(flow_dir)
    errors: list[str] = []

    # 1. config.yaml
    config_path = flow_dir / "config.yaml"
    if not config_path.exists():
        errors.append("config.yaml: file not found in .flow/")
        config_data = {}
    else:
        if yaml is None:
            errors.append("config.yaml: cannot parse (pyyaml not installed)")
            config_data = {}
        else:
            try:
                config_data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError as exc:
                errors.append(f"config.yaml: YAML parse error — {exc}")
                config_data = {}

    # 2. Guardrail files
    guardrail_cfg = config_data.get("guardrails", {}) if config_data else {}
    always_on: list[str] = guardrail_cfg.get("always_on", []) or []
    optional: list[str] = guardrail_cfg.get("optional", []) or []

    for name in always_on:
        # look in guardrails/always-on/<name>.md
        candidate = flow_dir / "guardrails" / "always-on" / f"{name}.md"
        if not candidate.exists():
            errors.append(
                f"guardrail '{name}': expected {candidate.relative_to(flow_dir)} not found"
            )

    for name in optional:
        candidate = flow_dir / "guardrails" / "optional" / f"{name}.md"
        if not candidate.exists():
            errors.append(
                f"guardrail '{name}': expected {candidate.relative_to(flow_dir)} not found"
            )

    # 3. playbook.md step references
    playbook_path = flow_dir / "playbook.md"
    if playbook_path.exists():
        playbook_text = playbook_path.read_text(encoding="utf-8")
        for m in _LOAD_REF_RE.finditer(playbook_text):
            rel_path = m.group(1)
            abs_path = flow_dir / rel_path
            if not abs_path.exists():
                errors.append(
                    f"playbook.md references '{rel_path}' which does not exist"
                )

    return errors


def main(argv: list[str] | None = None) -> int:
    args = (argv or sys.argv)[1:]
    repo_root = find_repo_root()
    flow_dir = Path(args[0]) if args else repo_root / ".flow"

    errors = check(flow_dir)
    if errors:
        print("structure-check FAILED:")
        for e in errors:
            print(f"  {e}")
        return 1
    print("structure-check OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
