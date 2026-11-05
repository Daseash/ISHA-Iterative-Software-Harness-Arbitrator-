"""P0-12: traceback_sig learnable writeback."""

from src.bench.classify import _traceback_sig


def test_sig_extracts_error_and_frame(tmp_path):
    log = tmp_path / "inst"
    log.mkdir()
    (log / "test_output.txt").write_text(
        'FAIL: test_x\nTraceback:\n  File "/repo/mod.py", line 12, in func\nTypeError: len(None)\n',
        encoding="utf-8",
    )
    assert _traceback_sig(log, {}) == "TypeError @ mod.py::func"


def test_sig_empty_when_no_failure():
    assert _traceback_sig(None, {}) == ""


def test_breakdown_writes_learnable_rows(monkeypatch, tmp_path):
    import json

    from src.bench import classify as cl

    monkeypatch.setenv("ISHA_MEMORY_DB", str(tmp_path / "m.db"))
    run = tmp_path / "run1"
    inst = run / "a__b-1"
    inst.mkdir(parents=True)
    (inst / "meta.json").write_text(json.dumps({
        "instance_id": "a__b-1", "status": "done", "attempts": 1,
        "model_patch": "diff", "test_output": "TypeError: boom",
    }), encoding="utf-8")
    records = [{"instance_id": "a__b-1", "repo": "a/b", "patch": ""}]
    bd = cl.build_breakdown(run, records, {"resolved_ids": []})
    assert bd["rows"][0]["category"] == "tests_failed"
    from src.memory import store as mem

    row = mem.fetch("a__b-1")
    assert row is not None and row["resolved"] == 0
    assert row["fail_bucket"] == "tests_failed"
    assert "TypeError" in (row["traceback_sig"] or "")
