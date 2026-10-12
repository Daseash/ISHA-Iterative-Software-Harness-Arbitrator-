"""
ISHA Session 5 — Wave 4 Targeted Rescue Pipeline
Runs the 9 remaining unpatched instances using the 6 Gemini API keys
and the multi-model tournament (Gemini Flash + Qwen 2.5 Coder + DeepSeek Chat).
Merges any clean patches into results/lite300-s5.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

def main():
    slice_file = ROOT / "data" / "slices" / "lite300-s5-r4.json"
    if not slice_file.is_file():
        print(f"Error: Slice file {slice_file} not found!")
        return

    instances = json.loads(slice_file.read_text(encoding="utf-8"))
    print(f"\n[pipeline] Launching Wave 4 rescue for {len(instances)} remaining unpatched instances...", flush=True)

    cmd = [
        PYTHON, "-m", "src.bench.runner",
        "--run-id", "lite300-s5-r4",
        "--instances", *instances,
        "--candidates", "3",
        "--workers", "1",
        "--timeout", "500",
        "--max-retries", "2",
    ]

    res = subprocess.run(cmd, cwd=str(ROOT))
    print(f"\n[pipeline] Wave 4 runner finished with code: {res.returncode}", flush=True)

    # Automatically merge into results/lite300-s5
    print("\n[pipeline] Merging newly rescued patches into results/lite300-s5...", flush=True)
    merge_cmd = [
        PYTHON, "scripts/merge_predictions.py",
        "--source", "results/lite300-s5-r4",
        "--target", "results/lite300-s5",
    ]
    subprocess.run(merge_cmd, cwd=str(ROOT))

    # Report updated patch yield
    pred_file = ROOT / "results" / "lite300-s5" / "predictions.json"
    if pred_file.is_file():
        preds = json.loads(pred_file.read_text(encoding="utf-8"))
        non_empty = [p for p in preds if p.get("model_patch", "").strip()]
        print(f"\n[pipeline] Session 5 Total Clean Patches: {len(non_empty)}/30 ({len(non_empty)/30*100:.1f}%)", flush=True)

if __name__ == "__main__":
    main()
