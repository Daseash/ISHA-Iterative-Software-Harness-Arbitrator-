"""Label collector truth + safety (2026-10-16 incident).

1. Stale summary truth: collect_run must union resolved ids from per-instance
   official report.json files (score.py parity), not just the summary
   harness_report.json — lite300-s5's summary said 0 while per-instance
   reports proved 3, which would have mislabeled 3 true resolves as failures.
2. Dry-run safety: --dry-run once DELETED the whole label store (unlink ran
   before the dry-run guard). A dry run must never mutate.
3. Synthetic-clobber guard: build_laya_labels (synthetic bootstrap) refuses
   to overwrite a non-empty real store without --force.
"""

import json
from pathlib import Path

import pytest

from src.bench.label_collect import collect_run, main


def _run(tmp_path: Path, name: str, resolved_in_report: list[str]) -> Path:
    run = tmp_path / name
    (run / "django__django-11099").mkdir(parents=True)
    (run / "django__django-11099" / "meta.json").write_text(
        json.dumps({
            "instance_id": "django__django-11099",
            "status": "done",
            "model_patch": "diff --git a/x b/x\n",
            "laya_scores": {"fix_quality": 2, "matches_issue": 1,
                            "safe_to_apply": 1},
            "repro": {},
        }),
        encoding="utf-8",
    )
    # Stale summary: knows nothing.
    (run / "harness_report.json").write_text(
        json.dumps({"resolved_ids": []}), encoding="utf-8")
    # Official per-instance truth.
    deep = run / "logs" / "run_evaluation" / name / "ISHA" / "django__django-11099"
    deep.mkdir(parents=True)
    (deep / "report.json").write_text(
        json.dumps({i: {"resolved": i in resolved_in_report}
                    for i in ["django__django-11099"]}),
        encoding="utf-8",
    )
    return run


def test_stale_summary_overruled_by_report_json(tmp_path):
    _run(tmp_path, "lite300-s9", ["django__django-11099"])
    rows, stats = collect_run("lite300-s9", results=tmp_path)
    assert stats["resolved"] == 1
    assert len(rows) == 1 and rows[0]["label"] == 1


def test_sibling_suffix_dirs_union(tmp_path):
    _run(tmp_path, "lite300-s9", [])
    r2 = tmp_path / "lite300-s9-r2"
    r2.mkdir()
    (r2 / "harness_report.json").write_text(
        json.dumps({"resolved_ids": ["django__django-11099"]}),
        encoding="utf-8")
    rows, stats = collect_run("lite300-s9", results=tmp_path)
    assert stats["resolved"] == 1
    assert rows and all(r["label"] == 1 for r in rows)


def test_dry_run_never_mutates_store(tmp_path):
    store = tmp_path / "labels.jsonl"
    store.write_text('{"label": 1}\n', encoding="utf-8")
    _run(tmp_path, "lite300-s9", ["django__django-11099"])
    import src.bench.label_collect as lc

    real_results = lc.RESULTS
    lc.RESULTS = tmp_path
    try:
        rc = main(["--run-id", "lite300-s9", "--dry-run",
                   "--out", str(store)])
    finally:
        lc.RESULTS = real_results
    assert rc == 0
    assert store.read_text(encoding="utf-8") == '{"label": 1}\n'


def test_synthetic_builder_refuses_clobber():
    from src.bench import build_laya_labels as bll

    with pytest.raises(SystemExit, match="REFUSING"):
        bll.build_labels()
