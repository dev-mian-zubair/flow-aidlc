#!/usr/bin/env python3
"""Bump the flow-aidlc version in lockstep across its three sources of truth.

The version lives in three files that MUST stay equal — the upgrade path stamps
``__version__`` into every instance's ``.flow/VERSION``, and the engine seed must
match so ``flow init`` and ``flow upgrade`` agree:

  1. ``pyproject.toml``                    -> ``version = "X.Y.Z"``
  2. ``src/flow_aidlc/__init__.py``        -> ``__version__ = "X.Y.Z"``
  3. ``src/flow_aidlc/engine/flow/VERSION`` -> ``X.Y.Z``

Usage::

    python scripts/bump_version.py 0.1.1      # set an explicit version
    python scripts/bump_version.py --patch    # 0.1.0 -> 0.1.1
    python scripts/bump_version.py --minor    # 0.1.0 -> 0.2.0
    python scripts/bump_version.py --major    # 0.1.0 -> 1.0.0
    python scripts/bump_version.py --check    # verify the three agree; exit 1 if not

Stdlib only, no third-party deps. Safe to run repeatedly (idempotent for a given
target version). Does NOT build, commit, tag, or upload — it only edits the three
files and prints the next steps.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Repo root = parent of this scripts/ directory.
ROOT = Path(__file__).resolve().parent.parent

_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
_PYPROJECT_RE = re.compile(r'(?m)^(version\s*=\s*")([^"]+)(")')
_INIT_RE = re.compile(r'(?m)^(__version__\s*=\s*")([^"]+)(")')


def _paths(root: Path) -> dict[str, Path]:
    return {
        "pyproject": root / "pyproject.toml",
        "init": root / "src" / "flow_aidlc" / "__init__.py",
        "engine": root / "src" / "flow_aidlc" / "engine" / "flow" / "VERSION",
    }


def read_versions(root: Path = ROOT) -> dict[str, str]:
    """Return the version string currently recorded in each of the three files."""
    p = _paths(root)
    py = _PYPROJECT_RE.search(p["pyproject"].read_text(encoding="utf-8"))
    ini = _INIT_RE.search(p["init"].read_text(encoding="utf-8"))
    if not py:
        raise ValueError(f'no `version = "..."` line in {p["pyproject"]}')
    if not ini:
        raise ValueError(f'no `__version__ = "..."` line in {p["init"]}')
    return {
        "pyproject": py.group(2),
        "init": ini.group(2),
        "engine": p["engine"].read_text(encoding="utf-8").strip(),
    }


def current_version(root: Path = ROOT) -> str:
    """The single current version. Raises if the three files disagree."""
    versions = read_versions(root)
    unique = set(versions.values())
    if len(unique) != 1:
        detail = ", ".join(f"{k}={v}" for k, v in versions.items())
        raise SystemExit(f"version drift — the three files disagree: {detail}")
    return unique.pop()


def bump(version: str, level: str) -> str:
    """Compute the next version for a semver bump level (major|minor|patch)."""
    if not _SEMVER.match(version):
        raise SystemExit(f"cannot {level}-bump non-semver version {version!r}")
    major, minor, patch = (int(x) for x in version.split("."))
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    if level == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise SystemExit(f"unknown bump level: {level}")


def write_version(new: str, root: Path = ROOT) -> None:
    """Set all three files to *new* and verify they now agree."""
    if not _SEMVER.match(new):
        raise SystemExit(f"target version {new!r} is not X.Y.Z")
    p = _paths(root)
    p["pyproject"].write_text(
        _PYPROJECT_RE.sub(rf"\g<1>{new}\g<3>", p["pyproject"].read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    p["init"].write_text(
        _INIT_RE.sub(rf"\g<1>{new}\g<3>", p["init"].read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    p["engine"].write_text(f"{new}\n", encoding="utf-8")
    after = read_versions(root)
    if set(after.values()) != {new}:
        raise SystemExit(f"post-write mismatch: {after}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bump flow-aidlc's version in lockstep.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("version", nargs="?", help="explicit target version X.Y.Z")
    g.add_argument("--major", action="store_const", const="major", dest="level")
    g.add_argument("--minor", action="store_const", const="minor", dest="level")
    g.add_argument("--patch", action="store_const", const="patch", dest="level")
    g.add_argument("--check", action="store_true", help="verify the three agree; exit 1 if not")
    g.add_argument("--show", action="store_true", help="print the current version (errors on drift)")
    args = ap.parse_args(argv)

    if args.show:
        print(current_version())
        return 0

    if args.check:
        versions = read_versions()
        if len(set(versions.values())) == 1:
            print(f"version in sync: {next(iter(versions.values()))}")
            return 0
        detail = "\n".join(f"  {k:9} {v}" for k, v in versions.items())
        print("version DRIFT — files disagree:\n" + detail, file=sys.stderr)
        return 1

    old = current_version()
    new = args.version if args.version else bump(old, args.level)
    if new == old:
        print(f"already at {new} — nothing to do.")
        return 0
    write_version(new)
    print(f"bumped {old} -> {new} in:")
    for key, path in _paths(ROOT).items():
        print(f"  {key:9} {path.relative_to(ROOT)}")
    print(
        "\nnext (maintainer):\n"
        "  uv run --with pytest --with pyyaml python -m pytest -q     # green\n"
        "  git add -A && git commit -m 'release: v" + new + "'\n"
        "  rm -rf dist/ build/ && uv run --with build --with 'setuptools>=68' \\\n"
        "      --with wheel python -m build --no-isolation\n"
        "  uv run --with twine python -m twine check dist/*\n"
        "  uv run --with twine python -m twine upload dist/*          # YOUR token\n"
        "  git tag v" + new + " && git push --tags"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
