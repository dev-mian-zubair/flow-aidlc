"""Guards for the docs/flow artifact layout.

worklog/ and knowledge/ are scaffolded under docs/flow/. Two guards:
  1. the engine sweep is complete (no stray root-level instance paths), and
  2. `flow init` actually produces the new layout and still gates green.
"""
import re
import subprocess
from pathlib import Path

from flow_aidlc.checks import gate
from flow_aidlc.commands import init

_ENGINE = Path(__file__).resolve().parents[1] / "src" / "flow_aidlc" / "engine"

# A root-level artifact path (`worklog/` or `knowledge/`) that is NOT already
# under docs/flow (lookbehind rejects a preceding `/`), NOT a shell `$var`, and
# NOT the `knowledge-map` token (needs a trailing slash). Fixed-width lookbehind
# so Python's re accepts it.
_STRAY = re.compile(r"(?<![\w$/])(worklog|knowledge)/")


def test_engine_markdown_and_hooks_have_no_stray_root_paths():
    offenders = []
    for p in sorted(list(_ENGINE.rglob("*.md")) + list(_ENGINE.rglob("*.sh"))):
        for lineno, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if _STRAY.search(line):
                offenders.append(f"{p.relative_to(_ENGINE)}:{lineno}: {line.strip()}")
    assert not offenders, (
        "Root-level worklog/ or knowledge/ paths remain — everything the engine "
        "writes lives under docs/flow/ now:\n" + "\n".join(offenders)
    )


def test_init_scaffolds_docs_flow_and_gate_passes(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    assert init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)]) == 0
    # New layout present...
    assert (tmp_path / "docs/flow/worklog").is_dir()
    assert (tmp_path / "docs/flow/knowledge/map/README.md").exists()
    # ...and the old root-level dirs are not created.
    assert not (tmp_path / "worklog").exists()
    assert not (tmp_path / "knowledge").exists()
    # The quality gate still passes on the relocated instance.
    assert gate.run(tmp_path) == 0
