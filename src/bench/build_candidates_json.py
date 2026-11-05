"""
Compile results/candidates.json from run records for Stage D reporting.

Reports:
  - Per-candidate tournament records across all 3 model families
  - Which model wins most often
  - Which model never wins
  - Substitution count & rates
"""

from __future__ import annotations

import glob
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "results"
CANDIDATES_PATH = RESULTS_DIR / "candidates.json"

DEFAULT_MODELS = {
    "coder_default": "qwen3.8-27b",
    "minimal_diff": "qwen3.8-27b",
    "call_site_aware": "gpt-oss-120b",
    "root_cause_first": "gemini-3.8-flash",
    "defensive_fix": "qwen3.8-27b",
    "cross_file_audit": "gemini-3.8-flash",
}


def build_candidates_json() -> dict:
    records = []
    seen = set()

    for p in sorted(glob.glob(str(RESULTS_DIR / "after/*/meta.json"))):
        try:
            meta = json.loads(Path(p).read_text(encoding="utf-8"))
        except Exception:
            continue
        iid = meta.get("instance_id")
        if not iid or iid in seen:
            continue
        seen.add(iid)

        candidates = meta.get("candidates") or []
        selected = meta.get("selected_candidate") or {}
        winner_idx = selected.get("index")

        model_log = meta.get("model_log") or []
        coder_models = [m.get("model") for m in model_log if m.get("role") == "coder"]

        for cand in candidates:
            strat = cand.get("strategy", "minimal_diff")
            req_model = DEFAULT_MODELS.get(strat, "qwen3.8-27b")
            actual_model = cand.get("model") or (coder_models.pop(0) if coder_models else req_model)
            if not actual_model:
                actual_model = req_model

            substituted = (req_model != actual_model)
            won = (cand.get("index") == winner_idx) if winner_idx is not None else False
            repro = cand.get("repro") or {}

            records.append({
                "instance_id": iid,
                "candidate_index": cand.get("index", 1),
                "strategy": strat,
                "temperature": cand.get("temperature", 0.2),
                "requested_model": req_model,
                "model_used": actual_model,
                "substituted": substituted,
                "patch_applied": cand.get("apply_ok", False),
                "gate_passed": cand.get("gate_ok", False),
                "repro_passed": bool(repro.get("before_ok") and repro.get("after_ok")),
                "regression_count": cand.get("regression_count", 0),
                "diff_size": cand.get("added_lines", 0) + cand.get("removed_lines", 0),
                "laya_score": cand.get("laya_combined", 0.0),
                "won_selection": won,
                "timestamp": meta.get("started_at", time.time()),
            })

    CANDIDATES_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")

    # Aggregate tournament summary
    models_stat: dict = {}
    for r in records:
        m = r["model_used"]
        if m not in models_stat:
            models_stat[m] = {
                "evaluated": 0,
                "substituted": 0,
                "applied": 0,
                "gates_passed": 0,
                "repro_passed": 0,
                "won_selection": 0,
            }
        models_stat[m]["evaluated"] += 1
        if r["substituted"]:
            models_stat[m]["substituted"] += 1
        if r["patch_applied"]:
            models_stat[m]["applied"] += 1
        if r["gate_passed"]:
            models_stat[m]["gates_passed"] += 1
        if r["repro_passed"]:
            models_stat[m]["repro_passed"] += 1
        if r["won_selection"]:
            models_stat[m]["won_selection"] += 1

    most_wins = max(models_stat.items(), key=lambda t: t[1]["won_selection"])[0] if models_stat else "none"
    never_won = [m for m, s in models_stat.items() if s["won_selection"] == 0]

    summary = {
        "total_candidate_evaluations": len(records),
        "unique_instances": len(seen),
        "models": models_stat,
        "most_wins": most_wins,
        "never_won": never_won,
    }
    return summary


if __name__ == "__main__":
    res = build_candidates_json()
    print(json.dumps(res, indent=2))
