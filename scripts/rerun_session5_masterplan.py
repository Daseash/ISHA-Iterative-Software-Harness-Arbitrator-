"""
ISHA Master Plan: Session 5 Re-run & Docker Evaluation.

Executes the universal 2-pass resolution pipeline on Session 5 (30 instances across Matplotlib, Seaborn, Flask):
1. Runs multi-candidate tournament (--candidates 3) enforcing all 8 empirical container invariants:
   - minimal_diff: surgical 1-12 line edits
   - call_site_aware: caller-graph inspection
   - root_cause_first: root-cause invariant enforcement
2. Filters candidate patches through AST static compilation gates and in-loop repair.
3. Merges surviving high-confidence patches into results/lite300-s5/predictions.json.
4. Executes official Docker evaluation via src.bench.harness_eval when Docker daemon is responsive.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def check_docker_daemon() -> bool:
    try:
        res = subprocess.run(["docker", "version"], capture_output=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False


def run_session5_tournament() -> None:
    print("=" * 70, flush=True)
    print("[session5] LAUNCHING SESSION 5 TOURNAMENT RE-RUN (30 INSTANCES)", flush=True)
    print("   Enforcing 8 Empirical Container Invariants across 3 Candidates", flush=True)
    print("=" * 70, flush=True)

    slice_file = ROOT / "data" / "slices" / "lite300-s5.json"
    instances = json.loads(slice_file.read_text(encoding="utf-8"))

    cmd = [
        PYTHON, "-m", "src.bench.runner",
        "--run-id", "lite300-s5-v2",
        "--instances", *instances,
        "--candidates", "3",
        "--workers", "1",
        "--timeout", "500",
        "--max-retries", "2",
    ]
    print(f"[session5] Executing: {' '.join(cmd[:6])} ... ({len(instances)} instances)", flush=True)
    proc = subprocess.run(cmd, cwd=str(ROOT))
    if proc.returncode != 0:
        print(f"[session5] Warning: Runner exited with code {proc.returncode}", flush=True)

    # Merge newly synthesized patches into main predictions
    v2_dir = ROOT / "results" / "lite300-s5-v2"
    base_dir = ROOT / "results" / "lite300-s5"
    if v2_dir.exists():
        print("[session5] Merging improved tournament patches into results/lite300-s5/predictions.json...", flush=True)
        subprocess.run([
            PYTHON, "scripts/merge_predictions.py",
            "--source", str(v2_dir),
            "--target", str(base_dir),
        ], cwd=str(ROOT))

    # Commit and push Session 5
    try:
        subprocess.run(["git", "add", "results/lite300-s5/predictions.json"], cwd=str(ROOT))
        msg = "feat(bench): finalize Session 5 tournament patches (improvement loop)"
        res = subprocess.run(["git", "commit", "-m", msg], cwd=str(ROOT), capture_output=True, text=True)
        if res.returncode == 0:
            print("[session5] Committed updated Session 5 predictions.", flush=True)
            subprocess.run(["git", "push", "origin", "main"], cwd=str(ROOT))
    except Exception as exc:
        print(f"[session5] Git push notice: {exc}", flush=True)


def run_sessions_9_and_10() -> None:
    print("\n" + "=" * 70, flush=True)
    print("🚀 PROCEEDING TO SESSIONS 9 & 10 (FINAL 60 BENCHMARK INSTANCES)", flush=True)
    print("=" * 70, flush=True)

    cmd = [
        PYTHON, "scripts/run_all_sessions.py",
        "--start", "9",
        "--end", "10",
        "--cooldown", "30",
    ]
    subprocess.run(cmd, cwd=str(ROOT))


def run_docker_evaluation() -> None:
    print("\n" + "=" * 70, flush=True)
    print("[docker] CHECKING DOCKER TESTBED DAEMON FOR OFFICIAL EVALUATION", flush=True)
    print("=" * 70, flush=True)

    pred_file = ROOT / "results" / "lite300-s5" / "predictions.json"
    slice_file = ROOT / "data" / "slices" / "lite300-s5.json"

    if not pred_file.is_file():
        print(f"[docker] Error: Predictions file {pred_file} not found!", flush=True)
        return

    if not check_docker_daemon():
        print("[docker] Notice: Docker Desktop daemon is not currently active on host.", flush=True)
        print("[docker] Complete all patches first. Once Docker Desktop is opened, grade with:", flush=True)
        print(f"         python -m src.bench.harness_eval --predictions results/lite300-s5/predictions.json --dataset-slice data/slices/lite300-s5.json", flush=True)
        return

    print("[docker] Docker daemon confirmed ready! Launching official SWE-bench container grading...", flush=True)
    eval_cmd = [
        PYTHON, "-m", "src.bench.harness_eval",
        "--predictions", str(pred_file),
        "--dataset-slice", str(slice_file),
        "--max-workers", "2",
        "--timeout", "600",
    ]
    subprocess.run(eval_cmd, cwd=str(ROOT))


def main() -> None:
    # 1. Run Session 5 tournament improvement loop & merge best patches
    run_session5_tournament()

    # 2. Automatically progress through Sessions 9 and 10
    run_sessions_9_and_10()

    # 3. Check for Docker evaluation
    run_docker_evaluation()

    # 4. Display final master scorecard
    subprocess.run([PYTHON, "scripts/score.py"], cwd=str(ROOT))
    print("\n[master] All remaining benchmark instances and improvement loops completed!", flush=True)


if __name__ == "__main__":
    main()
