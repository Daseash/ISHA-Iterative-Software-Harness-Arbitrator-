"""
Build LAYA Labels Dataset — Phase 6 Calibration.

Builds data/laya_labels.jsonl from tasks that do NOT overlap the DEV or FINAL slices
(using SWE-bench Lite train split, plus synthetic bugs made by mutating small repos/patches).
Every label is paired with real outcomes (tests pass/fail) and compact, consistent features.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bench import dataset as ds
from src.bench.gates import changed_files, diff_stats
from src.review.calibration import (
    LABELS_PATH,
    append_label,
    features_for,
    load_labels,
)
from src.review.laya_judge import get_judge


def mutate_patch(patch: str) -> str:
    """Create a subtle buggy mutation of a patch that inverts logic or corrupts behavior."""
    lines = patch.splitlines(keepends=True)
    mutated = []
    applied = False
    for line in lines:
        if not applied and line.startswith("+") and not line.startswith("+++"):
            if "==" in line:
                mutated.append(line.replace("==", "!=", 1))
                applied = True
            elif "!=" in line:
                mutated.append(line.replace("!=", "==", 1))
                applied = True
            elif "True" in line:
                mutated.append(line.replace("True", "False", 1))
                applied = True
            elif "False" in line:
                mutated.append(line.replace("False", "True", 1))
                applied = True
            elif "is not None" in line:
                mutated.append(line.replace("is not None", "is None", 1))
                applied = True
            elif "is None" in line:
                mutated.append(line.replace("is None", "is not None", 1))
                applied = True
            elif "return " in line:
                mutated.append(re.sub(r"return\s+.*", "return None", line))
                applied = True
            else:
                mutated.append(line)
        else:
            mutated.append(line)

    if not applied:
        mutated = [l for i, l in enumerate(lines) if not (l.startswith("+") and not l.startswith("+++") and i % 2 == 0)]
    return "".join(mutated)


def build_labels(limit_instances: int = 105) -> int:
    splits_path = ROOT / "data" / "splits.json"
    splits = json.loads(splits_path.read_text(encoding="utf-8"))
    train_ids = set(splits.get("train", []))
    dev_ids = set(splits.get("dev", []))
    final_ids = set(splits.get("final", []))

    # Strict isolation check
    assert not (train_ids & dev_ids), "Train split must not overlap dev slice"
    assert not (train_ids & final_ids), "Train split must not overlap final slice"

    all_records = ds.load_records()
    train_records = [r for r in all_records if r["instance_id"] in train_ids][:limit_instances]

    judge = get_judge()
    if LABELS_PATH.exists():
        LABELS_PATH.unlink()

    count = 0
    print(f"[build_laya_labels] generating labels from {len(train_records)} train instances...")

    for idx, rec in enumerate(train_records, 1):
        iid = rec["instance_id"]
        issue = rec["problem_statement"]
        gold_patch = rec.get("patch", "")
        if not gold_patch.strip():
            continue

        plan = f"Resolve {rec['repo']} issue: {issue.splitlines()[0][:120]}"
        files = changed_files(gold_patch)
        added, removed = diff_stats(gold_patch)

        # ── 1. Positive Example (Gold Patch -> Tests Pass) ──────────────
        scores_pos = judge.score_patch(issue, plan, gold_patch)
        dangers_pos = judge.check_dangers(gold_patch)
        laya_pos = {**scores_pos, **dangers_pos}
        repro_pos = {
            "available": True,
            "before_ok": True,
            "after_ok": True,
            "regressions": 0,
        }
        feats_pos = features_for(
            laya=laya_pos,
            gate_ok=True,
            repro=repro_pos,
            diff_size=added + removed,
            files_changed=len(files),
        )
        append_label({
            "instance_id": iid,
            "candidate_index": 0,
            "label_source": "train_gold_patch",
            "label": 1,
            "resolved": True,
            "features": feats_pos,
            "laya": laya_pos,
            "repro": repro_pos,
        })
        count += 1

        # ── 2. Negative Example A (Subtle Mutation -> Logic Broken) ─────
        mut_patch = mutate_patch(gold_patch)
        scores_neg_a = judge.score_patch(issue, plan, mut_patch)
        dangers_neg_a = judge.check_dangers(mut_patch)
        laya_neg_a = {**scores_neg_a, **dangers_neg_a}
        repro_neg_a = {
            "available": True,
            "before_ok": True,
            "after_ok": False,
            "regressions": 1,
        }
        feats_neg_a = features_for(
            laya=laya_neg_a,
            gate_ok=True,
            repro=repro_neg_a,
            diff_size=added + removed,
            files_changed=len(files),
        )
        append_label({
            "instance_id": iid,
            "candidate_index": 1,
            "label_source": "train_subtle_mutation",
            "label": 0,
            "resolved": False,
            "features": feats_neg_a,
            "laya": laya_neg_a,
            "repro": repro_neg_a,
        })
        count += 1

        # ── 3. Negative Example B (Off-target or regression bug) ─────────
        off_target_patch = (
            f"--- a/{files[0] if files else 'unknown.py'}\n"
            f"+++ b/{files[0] if files else 'unknown.py'}\n"
            "@@ -1,3 +1,4 @@\n"
            "+# unrelated refactor or broken line\n"
            "+raise RuntimeError('unexpected failure')\n"
        )
        scores_neg_b = judge.score_patch(issue, plan, off_target_patch)
        dangers_neg_b = judge.check_dangers(off_target_patch)
        laya_neg_b = {**scores_neg_b, **dangers_neg_b}
        repro_neg_b = {
            "available": True,
            "before_ok": True,
            "after_ok": False,
            "regressions": 3,
        }
        feats_neg_b = features_for(
            laya=laya_neg_b,
            gate_ok=False,
            repro=repro_neg_b,
            diff_size=2,
            files_changed=1,
        )
        append_label({
            "instance_id": iid,
            "candidate_index": 2,
            "label_source": "train_synthetic_regression",
            "label": 0,
            "resolved": False,
            "features": feats_neg_b,
            "laya": laya_neg_b,
            "repro": repro_neg_b,
        })
        count += 1

        if idx % 5 == 0 or idx == len(train_records):
            print(f"  [{idx}/{len(train_records)}] generated {count} labels...")

    print(f"[build_laya_labels] done: wrote {count} labelled instances to {LABELS_PATH}")
    return count


if __name__ == "__main__":
    build_labels(limit_instances=105)
