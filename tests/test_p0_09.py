"""P0-09: runner fail-closed (corrupt regen, no_confident_fix, real model)."""

from src.bench.runner import _categorize_unsolved


def test_no_confident_fix_preserved():
    assert _categorize_unsolved({"escalation": "no confident fix"}, {"message": ""}) == "no_confident_fix"
    assert _categorize_unsolved({}, {"message": "no candidate survived verification"}) == "no_confident_fix"
    # timeout still wins
    assert _categorize_unsolved({"failure_category": "timeout"}, {"message": "no confident fix"}) == "timeout"


def test_write_predictions_real_model(tmp_path):
    import json

    from src.bench.runner import write_predictions

    inst = tmp_path / "a__b-1"
    inst.mkdir()
    (inst / "meta.json").write_text(json.dumps({
        "instance_id": "a__b-1",
        "status": "done",
        "model_patch": "diff",
        "model_log": [{"role": "coder", "model": "gemini-3.5-flash-lite"}],
    }), encoding="utf-8")
    out = write_predictions(tmp_path)
    preds = json.loads(out.read_text(encoding="utf-8"))
    assert preds[0]["model_name_or_path"] == "gemini-3.5-flash-lite"
