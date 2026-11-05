"""
Rebuild LAYA labels from REAL harness outcomes — closes the synthetic-label
loophole in the calibration numbers.

``src/bench/build_laya_labels.py`` builds labels from gold patches and
synthetic mutations: useful as a bootstrap, but the resulting ECE/Brier
numbers are only as strong as that label set.  This script does the honest
thing: it reads a finished benchmark run (patches ISHA actually produced,
graded by the official SWE-bench harness) and writes one label per graded
instance, using the harness verdict as the ground truth.

  * label = 1  — the produced patch resolved the instance (in
    ``harness_report.json → resolved_ids``)
  * label = 0  — the produced patch did not resolve it (applied but the
    official tests failed, or no usable patch)

Usage:
    python -m src.bench.relabel_laya --run-id lite300
    python -m src.bench.relabel_laya --run-id lite300 --include-synthetic

Outputs:
    data/laya_labels_real.jsonl   — the real label set (fresh each run)
    data/laya_combiner.json       — refitted combiner (old one is backed up
                                    to data/laya_combiner_synthetic.json when
                                    the previous labels were synthetic)
    results/calibration_real.json — audit artifact for the real-label fit
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bench import dataset as ds
from src.bench.gates import changed_files, diff_stats
from src.bench.harness_eval import load_official_report
from src.review.calibration import (
    LABELS_PATH,
    MODEL_PATH,
    append_label,
    features_for,
    fit,
    load_labels,
)

REAL_LABELS = ROOT / "data" / "laya_labels_real.jsonl"
REAL_ARTIFACT = ROOT / "results" / "calibration_real.json"


def _load_run_labels(run_dir: Path, report: dict) -> list[dict]:
    """One raw (patch, verdict, meta) row per graded instance in the run."""
    resolved_ids = set(report.get("resolved_ids", []))
    rows = []
    for meta_path in sorted(run_dir.glob("*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        iid = meta.get("instance_id")
        if not iid or meta.get("status") != "done":
            continue
        patch = meta.get("model_patch") or ""
        if not patch.strip():
            continue
        rows.append({"meta": meta, "instance_id": iid, "resolved": iid in resolved_ids})
    return rows


def build_labels(run_dir: Path, include_synthetic: bool = False) -> dict:
    report = load_official_report(run_dir)
    if not report:
        raise SystemExit(
            f"no harness report for {run_dir} — run "
            f"`python -m src.bench.harness_eval --run-id {run_dir.name}` first"
        )
    rows = _load_run_labels(run_dir, report)
    if not rows:
        raise SystemExit(f"no graded instances with a patch found in {run_dir}")

    records = {r["instance_id"]: r for r in ds.load_records()}

    judge = None
    try:
        from src.review.laya_judge import get_judge

        judge = get_judge()
        print("[relabel] LAYA judge available — scoring real patches")
    except Exception as exc:  # noqa: BLE001 — labels stay real, LAYA zeros
        print(f"[relabel] WARNING: LAYA judge unavailable ({exc}); "
              "LAYA features will be 0 for this label set")

    REAL_LABELS.unlink(missing_ok=True)
    counts = {"positive": 0, "negative": 0}

    for row in rows:
        meta, iid, resolved = row["meta"], row["instance_id"], row["resolved"]
        record = records.get(iid, {})
        issue = record.get("problem_statement", "")
        plan = meta.get("plan") or f"Resolve {record.get('repo', 'repo')} issue"
        patch = meta.get("model_patch", "")

        if judge is not None:
            try:
                laya = {**judge.score_patch(issue, plan, patch),
                        **judge.check_dangers(patch)}
            except Exception:  # noqa: BLE001
                laya = {"fix_quality": 0, "matches_issue": 0, "safe_to_apply": 0}
        else:
            laya = {"fix_quality": 0, "matches_issue": 0, "safe_to_apply": 0}

        patch_info = meta.get("patch_info") or {}
        gates = patch_info.get("gates") or {}
        gate_ok = bool(patch_info.get("applied")) and bool(
            (gates.get("compile", {}).get("ok")) or not gates
        )
        # Bench mode has no local RED/GREEN measurement: report repro as
        # unavailable instead of guessing. after_ok mirrors the harness verdict
        # so the feature vector carries the measured outcome.
        repro = {"available": False, "before_ok": False,
                 "after_ok": resolved, "regressions": 0}
        files = changed_files(patch)
        added, removed = diff_stats(patch)

        features = features_for(laya=laya, gate_ok=gate_ok, repro=repro,
                                diff_size=added + removed,
                                files_changed=len(files))
        append_label({
            "instance_id": iid,
            "candidate_index": 0,
            "label_source": "real_harness_outcome",
            "label": 1 if resolved else 0,
            "resolved": resolved,
            "features": features,
            "laya": laya,
            "repro": repro,
            "run_id": run_dir.name,
        }, path=REAL_LABELS)
        counts["positive" if resolved else "negative"] += 1

    if include_synthetic:
        for old in load_labels(LABELS_PATH):
            append_label(old, path=REAL_LABELS)
        counts["synthetic_added"] = len(load_labels(LABELS_PATH)) - len(rows)

    print(f"[relabel] {REAL_LABELS.name}: {counts['positive']} positive / "
          f"{counts['negative']} negative (real harness outcomes)")
    return {"labels": str(REAL_LABELS), "positive": counts["positive"],
            "negative": counts["negative"],
            "run_id": run_dir.name, "resolved_ids": sorted(report.get("resolved_ids", []))}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild LAYA labels from real SWE-bench harness outcomes")
    parser.add_argument("--run-id", required=True,
                        help="results/<run-id> with a finished harness evaluation")
    parser.add_argument("--include-synthetic", action="store_true",
                        help="also fold the synthetic label set into the fit")
    args = parser.parse_args()

    run_dir = ROOT / "results" / args.run_id
    if not run_dir.is_dir():
        print(f"Unknown run: {run_dir}")
        return 2

    summary = build_labels(run_dir, include_synthetic=args.include_synthetic)
    if summary["positive"] == 0 or summary["negative"] == 0:
        print("[relabel] one-class label set — cannot fit a combiner; "
              "collect more resolved instances first")
        return 1

    # Back up the current combiner only once, if it was fitted on synthetic data.
    if MODEL_PATH.is_file():
        backup = ROOT / "data" / "laya_combiner_synthetic.json"
        try:
            existing = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
            if "synthetic" not in str(existing.get("labels_source", "")) \
                    and existing.get("fitted") and not backup.exists():
                backup.write_text(MODEL_PATH.read_text(encoding="utf-8"),
                                  encoding="utf-8")
                print(f"[relabel] previous combiner backed up to {backup.name}")
        except ValueError:
            pass

    model = fit(path=REAL_LABELS, out=MODEL_PATH, artifact=REAL_ARTIFACT)
    keys = ("fitted", "n_total", "n_train", "n_val", "temperature",
            "val_ece_raw", "val_ece_scaled", "val_brier_raw", "val_brier_scaled",
            "threshold", "balanced_accuracy")
    print("[relabel] combiner: " + json.dumps(
        {k: model.get(k) for k in keys if k in model}, default=str))
    print(f"[relabel] artifacts: {MODEL_PATH}, {REAL_ARTIFACT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
