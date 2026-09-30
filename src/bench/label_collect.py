"""
ISHA Label Collector — Phase 6 of the SWE-bench upgrade.

The combiner in ``src/review/calibration.py`` is fitted on
``data/laya_labels.jsonl``, but the outcome it needs ("did this patch
actually resolve the instance?") does not exist while the agent is running:
only the official harness, afterwards, can say so.  So labels cannot be
collected *during* a run — they are collected here, by joining three
sources that a finished run leaves on disk:

    1. ``results/<run_id>/<instance>/meta.json``      candidate evidence
                                                       (LAYA scores, gate
                                                        result, diff size)
    2. ``results/<run_id>/<instance>/candidates.json`` per-candidate rows
    3. ``results/<run_id>/harness/harness_report.json`` the ground truth

The ground truth used here is the *instance* outcome, so with a run that
resolves nothing every label is 0.  ``fit()`` refuses to fit on such a set
rather than returning a confident model that predicts "never resolve".

    python -m src.bench.label_collect --run-id baseline
    python -m src.bench.label_collect --run-id baseline --run-id after --append
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.review.calibration import (  # noqa: E402
    LABELS_PATH,
    append_label,
    features_for,
    load_labels,
)
from src.bench.gates import changed_files, diff_stats  # noqa: E402

RESULTS = ROOT / "results"


def _read(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _candidates(meta: dict) -> list[dict]:
    """Every candidate the run considered, best first.

    Runs with a single candidate have no ``candidates.json``; the meta's own
    patch is then the only candidate and it still carries a LAYA score.
    """
    rows = meta.get("candidates")
    if isinstance(rows, list) and rows:
        return [r for r in rows if isinstance(r, dict)]
    patch = (meta.get("model_patch") or "").strip()
    if not patch:
        return []
    return [{
        "patch": patch,
        "valid": meta.get("status") == "done",
        "laya": meta.get("laya_scores") or {},
        "repro": meta.get("repro") or {},
    }]


def collect_run(run_id: str, results: Path = RESULTS) -> tuple[list[dict], dict]:
    """Build label rows for one finished run. Returns (rows, stats)."""
    run_dir = results / run_id
    if not run_dir.is_dir():
        return [], {"error": f"no such run: {run_dir}"}

    # harness_eval writes <run>/harness_report.json; older runs used
    # <run>/harness/harness_report.json.  Accept both or every label
    # comes back 0 and the combiner is fitted on pure noise.
    report = (
        _read(run_dir / "harness_report.json")
        or _read(run_dir / "harness" / "harness_report.json")
        or {}
    )
    resolved_ids = set(report.get("resolved_ids") or [])

    rows: list[dict] = []
    stats = {"run_id": run_id, "resolved": len(resolved_ids), "positives": 0,
             "instances": 0, "skipped": 0}

    for inst_dir in sorted(p for p in run_dir.iterdir() if p.is_dir()):
        meta = _read(inst_dir / "meta.json")
        if not meta or not meta.get("instance_id"):
            stats["skipped"] += 1
            continue
        stats["instances"] += 1
        iid = meta["instance_id"]
        resolved = iid in resolved_ids

        for idx, cand in enumerate(_candidates(meta)):
            patch = (cand.get("patch") or "").strip()
            if not patch:
                continue
            files = changed_files(patch)
            added, removed = diff_stats(patch)
            laya = cand.get("laya") or {}
            # LAYA's contract: a dict of sub-scores, or a flat object.
            if not isinstance(laya, dict):
                laya = {"fix_quality": laya}
            features = features_for(
                laya=laya,
                gate_ok=bool(cand.get("valid", True)),
                repro=cand.get("repro") or {},
                diff_size=added + removed,
                files_changed=len(files),
            )
            rows.append({
                "run_id": run_id,
                "instance_id": iid,
                "candidate_index": idx,
                "label_source": "harness_report",
                "label": 1 if resolved else 0,
                "resolved": resolved,
                "features": features,
            })
            if resolved:
                stats["positives"] += 1

    return rows, stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id", action="append", required=True,
                    help="run id to label (repeatable)")
    ap.add_argument("--out", default=str(LABELS_PATH))
    ap.add_argument("--append", action="store_true",
                    help="keep existing rows instead of starting a new store")
    ap.add_argument("--dry-run", action="store_true",
                    help="print what would be written")
    args = ap.parse_args(argv)

    out = Path(args.out)
    if not args.append and out.exists():
        out.unlink()

    all_rows: list[dict] = []
    for run_id in args.run_id:
        rows, stats = collect_run(run_id)
        all_rows.extend(rows)
        print(f"{run_id}: {stats.get('instances', 0)} instances, "
              f"{len(rows)} candidates, {stats.get('resolved', 0)} resolved, "
              f"{stats.get('skipped', 0)} without meta.json")

    for row in all_rows:
        if not args.dry_run:
            append_label(row, out)

    existing = len(load_labels(out)) if not args.dry_run else 0
    positives = sum(1 for r in all_rows if r["label"])
    print(f"{'would write' if args.dry_run else 'wrote'} {len(all_rows)} labels "
          f"({positives} positive) -> {out}")
    if not args.dry_run:
        print(f"label store now holds {existing} rows")

    if all_rows and positives == 0:
        print("WARNING: every label is 0 — this run resolved nothing, so the "
              "combiner cannot be fitted (fit() needs at least 8 labels with "
              "both classes).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
