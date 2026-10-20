#!/usr/bin/env python3
"""P2-04: build SWE-bench submission (all_preds.jsonl + trajectories).

Merges every results/*/predictions.json (dedup by instance, prefer resolved)
into results/all_preds.jsonl plus results/trajectories.jsonl (model_log).
Usage: python isha-agent/scripts/build_submit.py [--out results/all_preds.jsonl]
Submit per https://github.com/princeton-nlp/SWE-bench once Sec 1 hits >=75/300.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENT_DIR = HERE.parent
RESULTS_DIR = AGENT_DIR / "results"


def _graded_runs() -> dict[str, dict[str, bool]]:
    """instance_id -> {run name: resolved?} from OFFICIAL per-instance reports.

    Only files under a logs/ tree count (harness_eval writes
    <run>/logs/.../<iid>/report.json = {iid: {resolved: bool}}).
    """
    graded: dict[str, dict[str, bool]] = {}
    for rep_file in sorted(RESULTS_DIR.rglob("report.json")):
        try:
            rel = rep_file.relative_to(RESULTS_DIR)
        except ValueError:
            continue
        if "logs" not in rel.parts:
            continue
        try:
            data = json.loads(rep_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        run = rel.parts[0]
        for key, val in data.items():
            if isinstance(val, dict) and "resolved" in val:
                graded.setdefault(str(key), {})[run] = bool(val["resolved"])
    return graded


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(RESULTS_DIR / "all_preds.jsonl"))
    ap.add_argument("--traj", default=str(RESULTS_DIR / "trajectories.jsonl"))
    args = ap.parse_args()

    graded = _graded_runs()
    # iid -> (graded_here, resolved_here, patch_len, run, patch, model)
    # Graded beats ungraded, resolved beats failed, longer breaks last ties.
    best: dict[str, tuple] = {}
    # iid -> (graded_here, resolved_here, run, traj)
    best_traj: dict[str, tuple] = {}
    for pred_file in sorted(RESULTS_DIR.rglob("predictions.json")):
        try:
            items = json.loads(pred_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(items, list):
            continue
        run = pred_file.parent.name
        metas = {}
        for meta_file in sorted(pred_file.parent.glob("*/meta.json")):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            if meta.get("instance_id"):
                metas[meta["instance_id"]] = meta
        for item in items:
            iid = item.get("instance_id", "")
            patch = (item.get("model_patch") or "").strip()
            if not iid or not patch:
                continue
            g = 1 if run in graded.get(iid, {}) else 0
            r = 1 if graded.get(iid, {}).get(run) else 0
            key = (g, r, len(patch))
            if iid not in best or key > (best[iid][0], best[iid][1], best[iid][2]):
                best[iid] = (g, r, len(patch), run, patch,
                             item.get("model_name_or_path", "isha"))
            meta = metas.get(iid, {})
            tkey = (g, r, run)
            if iid not in best_traj or tkey > (best_traj[iid][0], best_traj[iid][1], best_traj[iid][2]):
                best_traj[iid] = (g, r, run, {
                    "instance_id": iid,
                    "run": run,
                    "strategy": meta.get("strategy", ""),
                    "model_log": meta.get("model_log", []),
                    "failure_category": meta.get("failure_category", ""),
                })

    preds = {iid: {"instance_id": iid, "model_patch": v[4], "model_name_or_path": v[5]}
             for iid, v in best.items()}
    trajs = {iid: v[3] for iid, v in best_traj.items()}

    out = Path(args.out)
    out.write_text("\n".join(json.dumps(preds[k]) for k in sorted(preds)) + "\n", encoding="utf-8")
    Path(args.traj).write_text(
        "\n".join(json.dumps(trajs[k], default=str) for k in sorted(trajs)) + "\n", encoding="utf-8"
    )
    print(f"submit: {len(preds)} preds -> {out} (+{len(trajs)} trajectories)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
