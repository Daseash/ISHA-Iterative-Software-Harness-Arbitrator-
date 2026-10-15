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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(RESULTS_DIR / "all_preds.jsonl"))
    ap.add_argument("--traj", default=str(RESULTS_DIR / "trajectories.jsonl"))
    args = ap.parse_args()

    preds: dict[str, dict] = {}
    trajs: dict[str, dict] = {}
    for pred_file in sorted(RESULTS_DIR.rglob("predictions.json")):
        try:
            items = json.loads(pred_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(items, list):
            continue
        run = pred_file.parent.name
        for item in items:
            iid = item.get("instance_id", "")
            patch = (item.get("model_patch") or "").strip()
            if not iid or not patch:
                continue
            # Prefer longest non-empty patch (proxy for resolved until graded).
            if iid not in preds or len(patch) > len(preds[iid].get("model_patch", "")):
                preds[iid] = {
                    "instance_id": iid,
                    "model_patch": patch,
                    "model_name_or_path": item.get("model_name_or_path", "isha"),
                }
        # Trajectory: meta.json model_log per instance in this run.
        for meta_file in sorted(pred_file.parent.glob("*/meta.json")):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            iid = meta.get("instance_id", "")
            if iid and iid not in trajs:
                trajs[iid] = {
                    "instance_id": iid,
                    "run": run,
                    "strategy": meta.get("strategy", ""),
                    "model_log": meta.get("model_log", []),
                    "failure_category": meta.get("failure_category", ""),
                }

    out = Path(args.out)
    out.write_text("\n".join(json.dumps(preds[k]) for k in sorted(preds)) + "\n", encoding="utf-8")
    Path(args.traj).write_text(
        "\n".join(json.dumps(trajs[k], default=str) for k in sorted(trajs)) + "\n", encoding="utf-8"
    )
    print(f"submit: {len(preds)} preds -> {out} (+{len(trajs)} trajectories)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
