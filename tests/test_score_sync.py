"""Ensure the human-readable SSOT sees every official score artifact."""

import json

from scripts import sync_making_better


def test_sync_reads_harness_and_resolved_ids(monkeypatch, tmp_path):
    run = tmp_path / "lite300-s6-rescue-v4"
    run.mkdir()
    (run / "harness_report.json").write_text(
        json.dumps({"resolved_ids": ["repo__issue-1"]}), encoding="utf-8"
    )
    (run / "ISHA.lite300-s6.json").write_text(
        json.dumps({"repo__issue-2": {"resolved": True}}), encoding="utf-8"
    )
    monkeypatch.setattr(sync_making_better, "RESULTS_DIR", tmp_path)

    assert sync_making_better.scan_session("lite300-s6") == {
        "repo__issue-1",
        "repo__issue-2",
    }
