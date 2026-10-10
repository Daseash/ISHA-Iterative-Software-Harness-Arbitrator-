"""
ISHA Multi-Session Rescue Pipeline

Runs the improvement/rescue loop sequentially on unpatched instances across
Sessions 1, 2, and 3 using the 3-Candidate Tournament with dual-key Gemini rotation,
and merges all clean patches into their respective session prediction files.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

RESCUE_STEPS = [
    {
        "session": "lite300-s1",
        "run_id": "lite300-s1-r2",
        "slice_file": ROOT / "data" / "slices" / "lite300-s1-rescue.json",
        "target_pred": ROOT / "results" / "lite300-s1",
    },
    {
        "session": "lite300-s2",
        "run_id": "lite300-s2-r2",
        "slice_file": ROOT / "data" / "slices" / "lite300-s2-rescue.json",
        "target_pred": ROOT / "results" / "lite300-s2",
    },
    {
        "session": "lite300-s3",
        "run_id": "lite300-s3-r2",
        "slice_file": ROOT / "data" / "slices" / "lite300-s3-rescue.json",
        "target_pred": ROOT / "results" / "lite300-s3",
    },
]


def run_cmd(cmd: list[str]) -> int:
    print(f"\n[pipeline] Running: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(ROOT))
    return proc.returncode


def main() -> None:
    print("=" * 60)
    print("ISHA S1, S2, S3 Multi-Session Improvement & Rescue Pipeline")
    print("=" * 60)

    # First merge any completed Session 4 rescue patches
    s4_source = ROOT / "results" / "lite300-s4-rescue"
    s4_target = ROOT / "results" / "lite300-s4"
    if s4_source.is_dir() and (s4_target / "predictions.json").is_file():
        print("[pipeline] Syncing latest Session 4 rescue patches...")
        run_cmd([PYTHON, "scripts/merge_predictions.py", "--source", str(s4_source), "--target", str(s4_target)])

    for step in RESCUE_STEPS:
        run_id = step["run_id"]
        slice_file = step["slice_file"]
        target_dir = step["target_pred"]
        session_name = step["session"]

        if not slice_file.is_file():
            print(f"[pipeline] Skipping {run_id}: slice {slice_file} not found.")
            continue

        instances = json.loads(slice_file.read_text(encoding="utf-8"))
        print(f"\n>>> Starting Rescue for {session_name} ({len(instances)} instances)")
        print(f"    Instances: {instances}")

        runner_cmd = [
            PYTHON, "-m", "src.bench.runner",
            "--run-id", run_id,
            "--instances", *instances,
            "--candidates", "3",
            "--workers", "1",
            "--timeout", "500",
            "--max-retries", "2",
        ]
        rc = run_cmd(runner_cmd)
        print(f"[pipeline] {run_id} finished with return code {rc}")

        # Merge newly rescued patches into main session predictions
        merge_cmd = [
            PYTHON, "scripts/merge_predictions.py",
            "--source", f"results/{run_id}",
            "--target", f"results/{session_name}",
        ]
        run_cmd(merge_cmd)

    print("\n" + "=" * 60)
    print("ALL SESSIONS RESCUE PIPELINE COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
