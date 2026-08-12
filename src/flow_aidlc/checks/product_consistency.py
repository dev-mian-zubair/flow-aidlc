"""Product consistency — validates the Discover phase's product artifacts.

Each unit directory under ``docs/flow/product/`` must contain a well-formed
``progress.md`` with valid YAML frontmatter, and every checked (completed)
stage in the ``## Stages`` checklist must have the corresponding artifact file
present and containing the required sections.

Failure posture: if ``docs/flow/product/`` does not exist, return ``[]``
(skip silently). If pyyaml is unavailable, return a single blocking error.
Unparseable or structurally invalid frontmatter is reported per unit.

Usage:
    python -m flow_aidlc.checks.product_consistency            # uses repo root
    python -m flow_aidlc.checks.product_consistency <repo_root>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from flow_aidlc.checks._root import find_repo_root
from flow_aidlc.checks.artifact_sensor import required_sections

try:
    import yaml  # pyyaml
except ImportError:
    yaml = None  # type: ignore[assignment]


# Maps stage name → artifact filename
_STAGE_ARTIFACTS: dict[str, str] = {
    "vision": "vision.md",
    "pr-faq": "pr-faq.md",
    "research": "research.md",
    "prd": "prd.md",
    "roadmap": "roadmap.md",
}

# Required sections per artifact file
_ARTIFACT_SECTIONS: dict[str, list[str]] = {
    "vision.md": [
        "## Problem",
        "## Target users",
        "## North Star metric",
        "## Outcome / OKR",
        "## Non-goals",
    ],
    "pr-faq.md": [
        "## Press release",
        "## FAQ — internal",
        "## FAQ — customer",
        "## Riskiest assumptions",
    ],
    "research.md": [
        "## Research questions",
        "## Market & demand",
        "## Competitors",
        "## Recommended tech stack",
        "## Trade-offs",
        "## Open questions",
        "## Sources",
    ],
    "prd.md": [
        "## Problem",
        "## Users / personas",
        "## Success metrics",
        "## Story map",
        "## Scope",
        "## Non-goals",
        "## Key requirements",
        "## Milestones",
        "## Open questions",
    ],
    "roadmap.md": [
        "## Candidate epics",
        "## Now / Next / Later",
    ],
}

_VALID_KINDS = {"product", "feature", "increment"}
_VALID_STATUSES = {"in-discovery", "approved", "parked", "superseded"}


def _parse_frontmatter(text: str) -> tuple[dict | None, str | None]:
    """Parse YAML frontmatter between the first two ``---`` lines.

    Returns ``(data, error)``:
      - ``(dict, None)``  — parsed frontmatter.
      - ``(None, error)`` — missing frontmatter or parse failure.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "missing or malformed frontmatter (no leading '---')"

    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break

    if end is None:
        return None, "missing or malformed frontmatter (no closing '---')"

    fm_text = "\n".join(lines[1:end])
    try:
        data = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        return None, f"frontmatter YAML parse error — {exc}"

    if not isinstance(data, dict):
        return None, "frontmatter did not parse to a mapping"

    return data, None


def _checked_stages(body: str) -> list[str]:
    """Return stage names from checked items in the ``## Stages`` checklist.

    Matches lines of the form ``- [x] <stage>`` (case-insensitive ``x``).
    """
    stages: list[str] = []
    in_stages = False
    for line in body.splitlines():
        if re.match(r"^##\s+Stages", line):
            in_stages = True
            continue
        if in_stages:
            if re.match(r"^##\s+", line):
                break
            m = re.match(r"^\s*-\s+\[x\]\s+(.+)", line, re.IGNORECASE)
            if m:
                stages.append(m.group(1).strip())
    return stages


def check(repo_root: Path | str) -> list[str]:
    """Return a list of error strings (empty → all clear)."""
    repo_root = Path(repo_root)
    product_dir = repo_root / "docs" / "flow" / "product"

    if not product_dir.exists():
        return []

    if yaml is None:
        return ["product-consistency: pyyaml not installed — cannot verify product consistency"]

    errors: list[str] = []

    for unit_dir in sorted(product_dir.iterdir()):
        if not unit_dir.is_dir():
            continue
        progress = unit_dir / "progress.md"
        if not progress.exists():
            continue

        try:
            text = progress.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"product-consistency: {unit_dir.name}: could not read progress.md — {exc}")
            continue

        fm, fm_error = _parse_frontmatter(text)
        if fm_error:
            errors.append(f"product-consistency: {unit_dir.name}: {fm_error}")
            continue

        # Derive the label to use in error messages
        unit_id = fm.get("id") or unit_dir.name

        # ---- Frontmatter validity ----

        # id must be present and non-empty
        if not fm.get("id"):
            errors.append(f"product-consistency: {unit_id}: frontmatter 'id' is missing or empty")

        # kind must be in the valid set
        kind = fm.get("kind")
        if kind not in _VALID_KINDS:
            errors.append(
                f"product-consistency: {unit_id}: invalid kind '{kind}' "
                f"(must be one of {sorted(_VALID_KINDS)})"
            )

        # status must be in the valid set
        status = fm.get("status")
        if status not in _VALID_STATUSES:
            errors.append(
                f"product-consistency: {unit_id}: invalid status '{status}' "
                f"(must be one of {sorted(_VALID_STATUSES)})"
            )

        # non-product units must have a parent
        if kind != "product":
            parent = fm.get("parent")
            if not parent:
                errors.append(
                    f"product-consistency: {unit_id}: kind '{kind}' requires 'parent' to be set"
                )

        # ---- Stage ↔ artifact existence ----

        # Body is everything after the closing ---
        lines = text.splitlines()
        end_fm = None
        if lines and lines[0].strip() == "---":
            for i, line in enumerate(lines[1:], start=1):
                if line.strip() == "---":
                    end_fm = i
                    break
        body = "\n".join(lines[end_fm + 1:]) if end_fm is not None else text

        for stage in _checked_stages(body):
            artifact_name = _STAGE_ARTIFACTS.get(stage)
            if artifact_name is None:
                continue  # unknown stage — not our concern
            artifact_path = unit_dir / artifact_name
            if not artifact_path.exists():
                errors.append(
                    f"product-consistency: {unit_id}: stage '{stage}' is checked but "
                    f"{artifact_name} does not exist"
                )
                continue

            # Check required sections in the artifact
            try:
                artifact_text = artifact_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                errors.append(
                    f"product-consistency: {unit_id}: could not read {artifact_name} — {exc}"
                )
                continue

            req = _ARTIFACT_SECTIONS.get(artifact_name, [])
            missing = required_sections(artifact_text, req)
            for heading in missing:
                errors.append(
                    f"product-consistency: {unit_id}: {artifact_name} is missing section '{heading}'"
                )

        # ---- links resolve ----
        links = fm.get("links")
        if isinstance(links, dict):
            for link_key, link_file in links.items():
                if not link_file:
                    continue
                link_path = unit_dir / link_file
                if not link_path.exists():
                    errors.append(
                        f"product-consistency: {unit_id}: links.{link_key} → '{link_file}' does not exist"
                    )

    return errors


def main(argv: list[str] | None = None) -> int:
    args = (argv or sys.argv)[1:]
    repo_root = Path(args[0]) if args else find_repo_root()
    errors = check(repo_root)
    if errors:
        print("product-consistency FAILED:")
        for e in errors:
            print(f"  {e}")
        return 1
    print("product-consistency OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
