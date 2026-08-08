"""`flow guardrail add <name>` — author a new guardrail from the template.

Scaffolds ``.flow/guardrails/{always-on|optional}/<name>.md`` from the shipped
``always-on/TEMPLATE.md``, substituting a rule-id prefix into the example rule
ids so the new file passes ``guardrail_lint`` (it keeps ``## Rule`` +
``## Verification`` and gets concrete ``**<PREFIX>-NN**`` ids). The guardrail is
registered in ``.flow/config.yaml`` under ``guardrails.always_on`` (or
``optional`` with ``--optional``) via a *targeted line edit* that preserves the
file's comments — a full pyyaml round-trip would strip them. For always-on
additions we also regenerate the "Guardrail impact checklist" table in
``.flow/templates/requirements.tmpl.md`` so it has one row per invariant.

Usage:
    flow guardrail add <name> [--prefix PREFIX] [--optional] [--path DIR]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from flow_aidlc.checks._root import find_repo_root
from flow_aidlc.engine_assets import engine_dir

try:
    import yaml
except ImportError:  # pragma: no cover - pyyaml is a runtime dependency
    yaml = None  # type: ignore[assignment]

_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="flow guardrail",
        description="Author guardrails (`flow guardrail add <name>` / `--from <pack>` / `packs`).",
    )
    p.add_argument("action", help="`add` (author/install) or `packs` (list starter packs).")
    p.add_argument("name", nargs="?", help="Guardrail name (kebab-case) for a single `add`.")
    p.add_argument("--from", dest="from_pack", default=None, help="Install a whole starter pack by name.")
    p.add_argument("--prefix", default=None, help="Rule-id prefix (default: derived from name).")
    p.add_argument("--optional", action="store_true", help="Register under guardrails.optional.")
    p.add_argument("--path", default=None, help="Directory to search upward from for a .flow/ (default: cwd).")
    return p


def _packs_dir() -> Path:
    """The shipped starter-pack library (lives in the package, not per-instance)."""
    return engine_dir() / "guardrail-packs"


def _available_packs() -> dict[str, list[Path]]:
    """Map pack name -> its guardrail files (sorted). Empty if none ship."""
    base = _packs_dir()
    if not base.is_dir():
        return {}
    return {
        pack.name: sorted(p for p in pack.glob("*.md") if not p.name.endswith(".ask.md"))
        for pack in sorted(base.iterdir())
        if pack.is_dir()
    }


def _derive_prefix(name: str) -> str:
    """Derive a rule-id prefix from the first hyphen-part, up to 4 chars.

    ``budget-integrity`` -> ``BUD``; ``license-sku-gating`` -> ``LIC``. We take
    the leading letters of the first word (dropping non-letters) rather than one
    initial per part, so the prefix stays readable and pronounceable.
    """
    parts = [seg for seg in name.split("-") if seg]
    first = parts[0] if parts else name
    letters = "".join(ch for ch in first if ch.isalpha()).upper()
    return letters[:3] or "GRD"


def run(argv: list[str]) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2

    if args.action == "packs":
        return _list_packs()

    if args.action != "add":
        sys.stderr.write("usage: flow guardrail add <name> | add --from <pack> | packs\n")
        return 2

    # `add --from <pack>` installs a curated bundle instead of one scaffold.
    if args.from_pack:
        root = find_repo_root(args.path)
        flow_dir = root / ".flow"
        if not flow_dir.is_dir():
            print("not a Flow repo — run `flow init` first")
            return 2
        if yaml is None:
            sys.stderr.write("flow guardrail: pyyaml is required (pip install pyyaml).\n")
            return 2
        return _install_pack(root, flow_dir, args.from_pack, args.optional)

    if not args.name:
        sys.stderr.write("usage: flow guardrail add <name> | add --from <pack> | packs\n")
        return 2

    name = args.name
    if not _NAME_RE.match(name):
        sys.stderr.write(
            f"flow guardrail: '{name}' is not kebab-case "
            "(lowercase letters, digits, and hyphens only).\n"
        )
        return 2

    root = find_repo_root(args.path)
    flow_dir = root / ".flow"
    if not flow_dir.is_dir():
        print("not a Flow repo — run `flow init` first")
        return 2

    if yaml is None:
        sys.stderr.write("flow guardrail: pyyaml is required (pip install pyyaml).\n")
        return 2

    prefix = (args.prefix or _derive_prefix(name)).upper()

    subdir = "optional" if args.optional else "always-on"
    list_key = "optional" if args.optional else "always_on"
    guardrail_path = flow_dir / "guardrails" / subdir / f"{name}.md"

    if guardrail_path.exists():
        sys.stderr.write(f"flow guardrail: {guardrail_path.relative_to(root)} already exists.\n")
        return 1

    template_path = flow_dir / "guardrails" / "always-on" / "TEMPLATE.md"
    if not template_path.exists():
        sys.stderr.write(f"flow guardrail: template not found at {template_path}.\n")
        return 2

    body = _render_guardrail(template_path.read_text(encoding="utf-8"), name, prefix, args.optional)
    guardrail_path.parent.mkdir(parents=True, exist_ok=True)
    guardrail_path.write_text(body, encoding="utf-8")

    # Register in config.yaml via a comment-preserving targeted line edit.
    config_path = flow_dir / "config.yaml"
    _register_in_config(config_path, list_key, name)

    # Regenerate the requirements checklist only for always-on invariants.
    if not args.optional:
        always_on = _read_list(config_path, "always_on")
        tmpl_path = flow_dir / "templates" / "requirements.tmpl.md"
        if tmpl_path.exists():
            _regenerate_checklist(tmpl_path, always_on)

    rel = guardrail_path.relative_to(root)
    print(f"Created {rel}")
    print(f"Registered '{name}' under guardrails.{list_key} in .flow/config.yaml")
    print()
    print("Next steps:")
    print(
        f"  Edit `{rel}` — replace the [FILL] placeholders and cite real code "
        "in your repo. Then `flow check`."
    )
    return 0


# ---------------------------------------------------------------------------
# starter packs
# ---------------------------------------------------------------------------

def _list_packs() -> int:
    packs = _available_packs()
    if not packs:
        print("No guardrail starter packs are shipped with this build.")
        return 0
    print("Guardrail starter packs (install with `flow guardrail add --from <pack>`):\n")
    for pack, files in packs.items():
        print(f"  {pack}")
        for f in files:
            print(f"    - {f.stem}")
    return 0


def _install_pack(root: Path, flow_dir: Path, pack: str, optional: bool) -> int:
    """Copy every guardrail in a shipped pack into the instance and register it."""
    packs = _available_packs()
    if pack not in packs:
        available = ", ".join(packs) or "(none shipped)"
        sys.stderr.write(f"flow guardrail: unknown pack '{pack}'. Available: {available}\n")
        return 2

    subdir = "optional" if optional else "always-on"
    list_key = "optional" if optional else "always_on"
    dest_dir = flow_dir / "guardrails" / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    config_path = flow_dir / "config.yaml"

    installed: list[str] = []
    skipped: list[str] = []
    for src in packs[pack]:
        name = src.stem
        dest = dest_dir / f"{name}.md"
        if dest.exists():
            skipped.append(name)
            continue
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        _register_in_config(config_path, list_key, name)
        installed.append(name)

    if installed and not optional:
        tmpl = flow_dir / "templates" / "requirements.tmpl.md"
        if tmpl.exists():
            _regenerate_checklist(tmpl, _read_list(config_path, "always_on"))

    if installed:
        print(f"Installed pack '{pack}' into guardrails.{list_key}: " + ", ".join(installed))
    if skipped:
        print("Skipped (already present): " + ", ".join(skipped))
    if not installed and not skipped:
        print(f"Pack '{pack}' is empty.")
        return 0
    print("Run `flow check` to lint them; edit any rule to fit your codebase.")
    return 0


# ---------------------------------------------------------------------------
# rendering / editing helpers
# ---------------------------------------------------------------------------

def _render_guardrail(template: str, name: str, prefix: str, optional: bool) -> str:
    """Substitute the title, id-prefix hints, and example rule ids in the template."""
    text = template

    # Title heading — replace the [FILL: Guardrail Name] placeholder with the name.
    title = name.replace("-", " ").title()
    text = text.replace("# [FILL: Guardrail Name]", f"# {title}")

    # ID-prefix hint line.
    text = re.sub(
        r"\*\*ID prefix:\*\* \[FILL:[^\]]*\]",
        f"**ID prefix:** {prefix}",
        text,
    )

    # Enforcement label follows the chosen list.
    if optional:
        text = text.replace(
            "**Enforcement:** always-on (blocking)",
            "**Enforcement:** optional (opt-in)",
        )

    # Example rule ids: **[PREFIX]-01** -> **<PREFIX>-01**, etc.
    text = re.sub(r"\*\*\[PREFIX\]-(\d+)\*\*", rf"**{prefix}-\1**", text)
    # Any remaining bare [PREFIX]/<PREFIX> mentions in prose.
    text = text.replace("[PREFIX]", prefix).replace("<PREFIX>", prefix)

    return text


def _serialize_inline_list(values: list[str]) -> str:
    """Render a YAML inline flow list: ``[a, b, c]`` (empty -> ``[]``)."""
    return "[" + ", ".join(values) + "]"


_LIST_LINE_RE_CACHE: dict[str, re.Pattern[str]] = {}


def _list_line_re(key: str) -> re.Pattern[str]:
    pat = _LIST_LINE_RE_CACHE.get(key)
    if pat is None:
        # Match: <indent><key>:<space>[ ... ]<optional trailing comment>
        pat = re.compile(
            rf"^(?P<indent>\s*){re.escape(key)}:\s*(?P<value>\[[^\]]*\])(?P<trail>.*)$"
        )
        _LIST_LINE_RE_CACHE[key] = pat
    return pat


def _register_in_config(config_path: Path, key: str, name: str) -> None:
    """Append ``name`` to the ``key:`` inline list in config.yaml, comments intact.

    Parses only the list value on the matching line (so comments elsewhere are
    untouched), appends without duplicating, and re-serializes an inline flow list.
    """
    lines = config_path.read_text(encoding="utf-8").splitlines()
    pat = _list_line_re(key)
    for i, line in enumerate(lines):
        m = pat.match(line)
        if not m:
            continue
        current = yaml.safe_load(m.group("value")) or []
        if not isinstance(current, list):
            current = []
        if name not in current:
            current.append(name)
        rebuilt = f"{m.group('indent')}{key}: {_serialize_inline_list(current)}{m.group('trail')}"
        lines[i] = rebuilt
        break
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_list(config_path: Path, key: str) -> list[str]:
    """Read the ``guardrails.<key>`` list from config (full parse; read-only)."""
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    guardrails = data.get("guardrails", {}) or {}
    values = guardrails.get(key, []) or []
    return [str(v) for v in values]


_CHECKLIST_HEADER = "## Guardrail impact checklist"
_TABLE_HEADER = "| Invariant | Impact |"
_TABLE_SEP = "|-----------|--------|"
_NO_GUARDRAILS_ROW = "<!-- no always-on guardrails yet -->"


def _regenerate_checklist(tmpl_path: Path, always_on: list[str]) -> None:
    """Rewrite the checklist table body to one row per always-on guardrail.

    Keeps the section heading, prose, and the table header/separator; replaces
    only the row block between the separator and the next blank line / heading.
    """
    text = tmpl_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Find the checklist section, then the table separator inside it.
    try:
        sec_idx = next(i for i, ln in enumerate(lines) if ln.strip() == _CHECKLIST_HEADER)
    except StopIteration:
        return

    sep_idx = None
    for i in range(sec_idx, len(lines)):
        if lines[i].strip().startswith("|") and set(lines[i].strip()) <= set("|-: "):
            sep_idx = i
            break
        # stop if we hit the next section before finding a table
        if lines[i].strip().startswith("## ") and i != sec_idx:
            break
    if sep_idx is None:
        return

    # The row block runs from just after the separator up to (not including) the
    # first line that is blank or a new heading — i.e. everything table-shaped.
    end_idx = sep_idx + 1
    while end_idx < len(lines):
        stripped = lines[end_idx].strip()
        if stripped == "" or stripped.startswith("#"):
            break
        end_idx += 1

    if always_on:
        new_rows = [
            f"| {name} (see `guardrails/always-on/{name}.md`) | [Answer]: |"
            for name in always_on
        ]
    else:
        new_rows = [f"| {_NO_GUARDRAILS_ROW} | |"]

    rebuilt = lines[: sep_idx + 1] + new_rows + lines[end_idx:]
    tmpl_path.write_text("\n".join(rebuilt) + "\n", encoding="utf-8")
