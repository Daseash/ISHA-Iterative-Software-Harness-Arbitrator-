"""P0-02 scoreboard + P0-03 golden verifier acceptance."""

import importlib.util
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
SCORE_PATH = AGENT_DIR / "scripts" / "score.py"
GOLDEN_PATH = AGENT_DIR / "scripts" / "verify_golden.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_p0_02_score_scans_all_suffixes_and_live_footer():
    text = SCORE_PATH.read_text(encoding="utf-8")
    # Must glob session* (r3/r4/r5/rescue/v2), not just session + -r2
    assert 'glob(f"{session_id}*")' in text or 'f"{session_id}*"' in text
    assert "harness_report.json" in text
    assert "laya_combiner.json" in text
    assert "apply_failures" in text
    # Legacy denom must not claim 120 as SSOT
    assert "120" not in text or "300" in text


def test_p0_03_golden_real_verifier_negative():
    mod = _load(GOLDEN_PATH, "verify_golden_p0_03")
    # Empty patch must NOT be clean (negative test: emptied golden fails)
    ok, _ = mod.patch_is_clean("")
    assert ok is False
    ok2, _ = mod.patch_is_clean("not a diff at all")
    assert ok2 is False
    # Conflict markers must fail
    ok3, _ = mod.patch_is_clean("diff --git a/f b/f\n<<<<<<< HEAD\n+x\n")
    assert ok3 is False
    # Real run must be green on current tree (7/7 verified live)
    assert mod.check_golden_protection() is True
