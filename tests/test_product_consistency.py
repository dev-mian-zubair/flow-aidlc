from pathlib import Path

from flow_aidlc.checks.product_consistency import check


def _unit(tmp, fm, files):
    d = tmp / "docs/flow/product/acme"
    d.mkdir(parents=True)
    (d / "progress.md").write_text(fm, encoding="utf-8")
    for name, body in files.items():
        (d / name).write_text(body, encoding="utf-8")
    return d


_OK_FM = ("---\nid: acme\nkind: product\nparent: null\ngrounding: greenfield\n"
          "status: in-discovery\nsupersedes: null\nlinks: {vision: vision.md}\n---\n"
          "## Stages\n- [x] vision\n- [ ] pr-faq\n")

_VISION_OK = ("## Problem\nx\n## Target users\nx\n## North Star metric\nx\n"
              "## Outcome / OKR\nx\n## Non-goals\nx\n")


def test_clean_unit_passes(tmp_path):
    _unit(tmp_path, _OK_FM, {"vision.md": _VISION_OK})
    assert check(tmp_path) == []


def test_missing_artifact_for_checked_stage(tmp_path):
    _unit(tmp_path, _OK_FM, {})   # vision checked but vision.md absent
    errs = check(tmp_path)
    assert any("vision.md" in e for e in errs)


def test_bad_kind_flagged(tmp_path):
    fm = _OK_FM.replace("kind: product", "kind: widget")
    _unit(tmp_path, fm, {"vision.md": _VISION_OK})
    assert any("kind" in e for e in check(tmp_path))


def test_no_product_dir_is_skipped(tmp_path):
    assert check(tmp_path) == []


import subprocess
from flow_aidlc.commands import init
from flow_aidlc.checks import gate


def test_gate_runs_product_check(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    assert init.run(["--yes", "--repo", "o/n", "--path", str(tmp_path)]) == 0
    _unit(tmp_path, _OK_FM, {"vision.md": _VISION_OK})
    assert gate.run(tmp_path) == 0
    (tmp_path / "docs/flow/product/acme/vision.md").unlink()   # break it
    assert gate.run(tmp_path) == 1
