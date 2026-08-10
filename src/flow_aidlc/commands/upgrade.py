"""`flow upgrade` — refresh the packaged engine without touching the instance.

Walks the packaged engine tree and, for each file, computes its target path in
the installed repo (``engine/flow/*`` → ``.flow/*``, ``engine/claude/*`` →
``.claude/*``, ``engine/knowledge/*`` → ``knowledge/*``). The manifest classifies
every engine-relative path as ``engine`` (package-owned — replaced verbatim) or
``instance`` (the user's own guardrails / config / maps / decisions — NEVER
overwritten). A more specific ``engine`` glob wins over a broad ``instance`` dir,
so e.g. ``always-on/README.md`` stays engine even though the ``always-on/`` dir
is an instance seed.

Special cases:
  * ``*.tmpl.*`` files are skipped — the rendered instance files (``config.yaml``,
    ``knowledge-map.yaml``, ``.mcp.json``) are the user's and must not be clobbered.
  * ``claude/settings.json`` is RE-MERGED into the target's existing settings
    (append engine hooks, dedupe, preserve the user's keys) — never blindly copied.

``--dry-run`` prints every planned action and writes nothing. ``--force`` upgrades
even when the recorded ``.flow/VERSION`` already matches the package version.

Usage:
    flow upgrade [--path DIR] [--dry-run] [--force]
"""
from __future__ import annotations

import argparse
import fnmatch
import shutil
import sys
from pathlib import Path

from flow_aidlc import __version__
from flow_aidlc.checks._root import find_repo_root
from flow_aidlc.engine_assets import engine_dir, merge_settings

try:
    import yaml
except ImportError:  # pragma: no cover - pyyaml is a runtime dependency
    yaml = None  # type: ignore[assignment]

# engine/<top>/ maps onto the repo directory <target>/.
_TREE_TO_TARGET = {"flow": ".flow", "claude": ".claude", "knowledge": "docs/flow/knowledge"}
# settings.json is re-merged, not copied.
_SETTINGS_REL = "claude/settings.json"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="flow upgrade",
        description="Update engine assets without touching your instance.",
    )
    p.add_argument("--path", default=None, help="Target directory (default: current directory).")
    p.add_argument("--dry-run", action="store_true", help="Print planned actions; write nothing.")
    p.add_argument("--force", action="store_true", help="Upgrade even if already up to date.")
    return p


def run(argv: list[str]) -> int:
    args = _build_parser().parse_args(argv)

    root = find_repo_root(args.path)
    flow_dir = root / ".flow"
    if not flow_dir.is_dir():
        print("not a Flow repo — run `flow init` first")
        return 2

    if yaml is None:
        sys.stderr.write("flow upgrade: pyyaml is required (pip install pyyaml).\n")
        return 2

    eng = engine_dir()
    manifest = _load_manifest(eng / "manifest.yaml")

    old_version = _read_version(flow_dir / "VERSION")
    new_version = __version__
    if old_version == new_version and not args.force:
        print(f"already up to date (v{new_version})")
        return 0

    dry = args.dry_run

    updated = 0
    preserved = 0
    for src in sorted(p for p in eng.rglob("*") if p.is_file()):
        rel = src.relative_to(eng).as_posix()

        # Skip rendered-config templates — their rendered instance files are the user's.
        if _is_tmpl(src.name):
            print(f"skip-tmpl   {rel}")
            continue

        # settings.json is re-merged, not classified/copied.
        if rel == _SETTINGS_REL:
            target = _target_path(root, rel)
            if dry:
                print(f"MERGE       {rel} -> {_display(root, target)}")
            else:
                merge_settings(src, target)
                print(f"MERGE       {rel} -> {_display(root, target)}")
            updated += 1
            continue

        target = _target_path(root, rel)
        if target is None:
            # A file outside the three mapped trees (manifest.yaml, README.md at
            # engine root). `flow init` never copies these into a repo, so upgrade
            # leaves them alone too.
            continue

        if _classify(rel, manifest) == "instance":
            print(f"skip-inst   {rel}")
            preserved += 1
            continue

        # Engine-classified — copy over the target.
        if dry:
            print(f"UPDATE      {rel} -> {_display(root, target)}")
        else:
            _copy_engine_file(src, target)
            print(f"UPDATE      {rel} -> {_display(root, target)}")
        updated += 1

    # Record the new engine version.
    if not dry:
        (flow_dir / "VERSION").write_text(f"{new_version}\n", encoding="utf-8")

    _print_summary(old_version, new_version, updated, preserved, dry)
    return 0


# ---------------------------------------------------------------------------
# manifest classification
# ---------------------------------------------------------------------------

def _load_manifest(path: Path) -> dict[str, list[str]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {
        "engine": [str(g) for g in (data.get("engine") or [])],
        "instance": [str(g) for g in (data.get("instance") or [])],
    }


def _matches(rel: str, glob: str) -> bool:
    """True if the engine-relative path `rel` matches a manifest glob.

    ``**`` means "this directory and anything under it": a trailing ``/**`` also
    matches the directory prefix itself. fnmatch treats ``*`` greedily across
    ``/``, which is what we want for the ``**`` dir globs the manifest uses.
    """
    if fnmatch.fnmatch(rel, glob):
        return True
    if glob.endswith("/**"):
        prefix = glob[:-3]
        return rel == prefix or rel.startswith(prefix + "/")
    return False


def _classify(rel: str, manifest: dict[str, list[str]]) -> str:
    """Classify an engine-relative path as ``engine`` or ``instance``.

    A path is ``engine`` unless it matches an ``instance`` glob — but a more
    specific ``engine`` glob wins over a broad ``instance`` dir. "More specific"
    = the longer matching glob string (fewer wildcards, deeper path).
    """
    engine_hit = max(
        (g for g in manifest["engine"] if _matches(rel, g)),
        key=len,
        default=None,
    )
    instance_hit = max(
        (g for g in manifest["instance"] if _matches(rel, g)),
        key=len,
        default=None,
    )
    if instance_hit is None:
        return "engine"
    if engine_hit is None:
        return "instance"
    # Both match: the longer (more specific) glob wins; ties go to engine.
    return "engine" if len(engine_hit) >= len(instance_hit) else "instance"


# ---------------------------------------------------------------------------
# filesystem helpers
# ---------------------------------------------------------------------------

def _is_tmpl(name: str) -> bool:
    """True for rendered-config templates like ``config.tmpl.yaml``."""
    return ".tmpl." in name


def _target_path(root: Path, rel: str) -> Path | None:
    """Map an engine-relative path onto its installed-repo target, or None.

    ``flow/playbook.md`` -> ``<root>/.flow/playbook.md``; likewise ``claude/`` and
    ``knowledge/``. Returns None for paths outside the three mapped trees.
    """
    head, _, tail = rel.partition("/")
    dest_dir = _TREE_TO_TARGET.get(head)
    if dest_dir is None or not tail:
        return None
    return root / dest_dir / tail


def _copy_engine_file(src: Path, target: Path) -> None:
    """Copy an engine file over its target, creating parents; keep hooks executable."""
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)
    if target.suffix == ".sh" and target.parent.name == "hooks":
        mode = target.stat().st_mode
        target.chmod(mode | 0o111)


def _display(root: Path, target: Path) -> str:
    try:
        return str(target.relative_to(root))
    except ValueError:  # pragma: no cover - target always under root here
        return str(target)


def _read_version(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _print_summary(old: str, new: str, updated: int, preserved: int, dry: bool) -> None:
    banner = "Flow upgrade (dry-run) — nothing written." if dry else "Flow upgraded."
    verb = "would update" if dry else "updated"
    print()
    print(banner)
    print(f"  {updated} engine file(s) {verb}, {preserved} instance file(s) preserved.")
    print(f"  Version: {old or '?'} -> {new}")
