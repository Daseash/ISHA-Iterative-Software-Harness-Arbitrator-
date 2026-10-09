"""
ISHA Prediction Merge Utility

Merges patches from a rescue run into a parent session's predictions.json file.
Usage:
    python scripts/merge_predictions.py --source results/lite300-s4-rescue --target results/lite300-s4
"""

import argparse
import json
import sys
from pathlib import Path


def merge_predictions(source_dir: Path, target_dir: Path) -> None:
    source_pred_file = source_dir / "predictions.json"
    target_pred_file = target_dir / "predictions.json"

    if not target_pred_file.is_file():
        print(f"[error] Target predictions file {target_pred_file} does not exist.", file=sys.stderr)
        sys.exit(1)

    target_data = json.loads(target_pred_file.read_text(encoding="utf-8"))
    # Can be list or dict
    is_list = isinstance(target_data, list)
    target_map = {item["instance_id"]: item for item in target_data} if is_list else dict(target_data)

    source_patches = {}
    if source_pred_file.is_file():
        source_data = json.loads(source_pred_file.read_text(encoding="utf-8"))
        s_list = source_data if isinstance(source_data, list) else list(source_data.values())
        for item in s_list:
            patch = item.get("model_patch", "").strip()
            if patch:
                source_patches[item["instance_id"]] = patch

    # Also check per-instance patch.diff files in source_dir
    for p_file in source_dir.glob("*/patch.diff"):
        inst_id = p_file.parent.name
        content = p_file.read_text(encoding="utf-8").strip()
        if content:
            source_patches[inst_id] = content

    print(f"[merge] Found {len(source_patches)} patches in source {source_dir.name}")
    rescued_count = 0

    for inst_id, patch in source_patches.items():
        if inst_id in target_map:
            old_patch = target_map[inst_id].get("model_patch", "").strip()
            if not old_patch and patch:
                target_map[inst_id]["model_patch"] = patch
                rescued_count += 1
                print(f"  + Rescued: {inst_id} ({len(patch)} bytes)")
        else:
            # New instance not in target
            target_map[inst_id] = {
                "instance_id": inst_id,
                "model_name_or_path": "ISHA",
                "model_patch": patch,
            }
            rescued_count += 1
            print(f"  + Added: {inst_id} ({len(patch)} bytes)")

    if is_list:
        final_data = list(target_map.values())
    else:
        final_data = target_map

    target_pred_file.write_text(json.dumps(final_data, indent=2, ensure_ascii=False), encoding="utf-8")
    
    clean_total = sum(1 for item in (final_data if is_list else final_data.values()) if item.get("model_patch", "").strip())
    total_inst = len(final_data)
    yield_pct = (clean_total / total_inst * 100) if total_inst else 0

    print(f"\n[merge] Merged {rescued_count} patches into {target_pred_file.name}")
    print(f"[merge] New Total: {clean_total} / {total_inst} clean patches ({yield_pct:.1f}% yield)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    merge_predictions(args.source, args.target)
