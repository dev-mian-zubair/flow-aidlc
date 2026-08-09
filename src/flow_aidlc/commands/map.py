"""`flow map add <glob> <doc>` — scaffold a knowledge-map doc + register it.

Creates ``knowledge/map/<doc>.md`` with provenance frontmatter (``status``,
``derives-from``, ``verified-at-sha`` pinned to the current short HEAD) and
appends a ``maps[]`` entry to ``.flow/knowledge-map.yaml`` pairing the doc with
the code glob it summarizes. Existing entries and comments are preserved; a
``maps: []`` seed is upgraded to a real list.

Usage:
    flow map add <glob> <doc> [--title T] [--path DIR]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from flow_aidlc.checks._root import find_repo_root
from flow_aidlc.paths import KNOWLEDGE_DIR


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="flow map",
        description="Manage knowledge maps (e.g. `flow map add <glob> <doc>`).",
    )
    p.add_argument("action", help="The action to perform (only `add` is supported).")
    p.add_argument("glob", nargs="?", help="Code path glob the doc derives from (e.g. backend/**).")
    p.add_argument("doc", nargs="?", help="Map doc slug (kebab-case, no extension).")
    p.add_argument("--title", default=None, help="Human title for the doc heading.")
    p.add_argument("--path", default=None, help="Directory to search upward from for a .flow/ (default: cwd).")
    return p


def _short_head(root: Path) -> tuple[str, bool]:
    """Return (short-sha, ok). ok=False → not a git repo / no commits."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
        )
    except OSError:
        return "UNKNOWN", False
    sha = result.stdout.strip()
    if result.returncode != 0 or not sha:
        return "UNKNOWN", False
    return sha, True


def run(argv: list[str]) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2

    if args.action != "add":
        sys.stderr.write("usage: flow map add <glob> <doc> [--title T]\n")
        return 2

    if not args.glob or not args.doc:
        sys.stderr.write("usage: flow map add <glob> <doc> [--title T]\n")
        return 2

    root = find_repo_root(args.path)
    flow_dir = root / ".flow"
    if not flow_dir.is_dir():
        print("not a Flow repo — run `flow init` first")
        return 2

    glob = args.glob
    doc = args.doc
    doc_path = root / KNOWLEDGE_DIR / "map" / f"{doc}.md"

    if doc_path.exists():
        sys.stderr.write(f"flow map: {doc_path.relative_to(root)} already exists.\n")
        return 1

    sha, ok = _short_head(root)
    if not ok:
        sys.stderr.write(
            "WARNING: could not resolve HEAD (not a git repo or no commits) — "
            "using UNKNOWN for verified-at-sha.\n"
        )

    title = args.title or doc
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(_doc_body(glob, sha, title), encoding="utf-8")

    map_file = flow_dir / "knowledge-map.yaml"
    _register_map(map_file, doc, glob)

    rel = doc_path.relative_to(root)
    print(f"Created {rel} (status: FRESH, verified-at-sha: {sha})")
    print("Registered the map entry in .flow/knowledge-map.yaml")
    print()
    print("Next steps:")
    print(f"  Edit `{rel}` — replace the one-line description with a real summary")
    print("  of the mapped code. Then `flow check`.")
    return 0


def _doc_body(glob: str, sha: str, title: str) -> str:
    return (
        "---\n"
        "status: FRESH\n"
        f"derives-from: [{glob}]\n"
        f"verified-at-sha: {sha}\n"
        "---\n"
        "\n"
        f"# {title}\n"
        "\n"
        "<One-line description — fill this in.>\n"
    )


def _register_map(map_file: Path, doc: str, glob: str) -> None:
    """Append a ``maps[]`` entry, preserving existing entries + comments.

    Handles the two shapes the file can take: a ``maps: []`` seed (replace the
    inline empty list with a block list) and an existing block list (append a
    new item at the end of the ``maps:`` block).
    """
    doc_rel = f"docs/flow/knowledge/map/{doc}.md"
    entry_line = f"  - {{ doc: {doc_rel}, derives-from: [{glob}] }}"

    text = map_file.read_text(encoding="utf-8")
    lines = text.splitlines()

    maps_idx = next(
        (i for i, ln in enumerate(lines) if ln.lstrip().startswith("maps:")), None
    )

    if maps_idx is None:
        # No maps: key at all — append a fresh block.
        suffix = "" if text.endswith("\n") else "\n"
        map_file.write_text(text + suffix + "maps:\n" + entry_line + "\n", encoding="utf-8")
        return

    maps_line = lines[maps_idx]
    after = maps_line.split("maps:", 1)[1].strip()

    if after in ("[]", "[ ]"):
        # Seed form `maps: []` → replace with a block list carrying one item.
        # Preserve any trailing comment on the maps: line.
        comment = ""
        if "#" in after:
            comment = " " + after[after.index("#"):]
        lines[maps_idx] = "maps:" + comment
        lines.insert(maps_idx + 1, entry_line)
        map_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    # Existing block list — find the end of the maps: block and append there.
    insert_at = len(lines)
    for i in range(maps_idx + 1, len(lines)):
        stripped = lines[i].strip()
        # A top-level (non-indented, non-comment, non-blank) line ends the block.
        if stripped and not lines[i].startswith((" ", "\t")) and not stripped.startswith("#"):
            insert_at = i
            break
    lines.insert(insert_at, entry_line)
    map_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
