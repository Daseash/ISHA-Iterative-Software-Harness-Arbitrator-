"""Submit-bundle integrity: the bundle must carry the GRADED patch.

Regression (2026-10-16): dedup preferred the LONGEST patch, so
django__django-11099 would have submitted an ungraded 1261-char baseline
patch instead of the graded 895-char s1 patch that actually resolved.
Selection order is now graded > resolved > longest.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_submit import RESULTS_DIR as _REAL_RESULTS  # noqa: E402
import build_submit as bs  # noqa: E402


def _run(results: Path, name: str, iid: str, patch: str,
         resolved=None) -> None:
    run = results / name
    (run / iid).mkdir(parents=True)
    (run / "predictions.json").write_text(json.dumps([{
        "instance_id": iid, "model_patch": patch,
        "model_name_or_path": "isha"}]), encoding="utf-8")
    if resolved is not None:
        deep = run / "logs" / "run_evaluation" / name / "ISHA" / iid
        deep.mkdir(parents=True)
        (deep / "report.json").write_text(
            json.dumps({iid: {"resolved": resolved}}), encoding="utf-8")


def test_graded_resolved_beats_longer_ungraded(tmp_path, monkeypatch):
    results = tmp_path / "results"
    _run(results, "run-old", "a__a-1", "x" * 2000)  # long, never graded
    _run(results, "run-new", "a__a-1", "diff --git short",
         resolved=True)  # graded + resolved
    monkeypatch.setattr(bs, "RESULTS_DIR", results)
    out = tmp_path / "all.jsonl"
    traj = tmp_path / "traj.jsonl"
    monkeypatch.setattr(sys, "argv", ["build_submit", "--out", str(out),
                                      "--traj", str(traj)])
    assert bs.main() == 0
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1 and rows[0]["model_patch"] == "diff --git short"


def test_ungraded_falls_back_to_longest(tmp_path, monkeypatch):
    results = tmp_path / "results"
    _run(results, "run-a", "b__b-2", "short")
    _run(results, "run-b", "b__b-2", "much longer patch here")
    monkeypatch.setattr(bs, "RESULTS_DIR", results)
    out = tmp_path / "all.jsonl"
    traj = tmp_path / "traj.jsonl"
    monkeypatch.setattr(sys, "argv", ["build_submit", "--out", str(out),
                                      "--traj", str(traj)])
    assert bs.main() == 0
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1 and rows[0]["model_patch"] == "much longer patch here"
