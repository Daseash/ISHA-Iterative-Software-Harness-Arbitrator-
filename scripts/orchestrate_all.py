"""
ISHA Master Benchmark Orchestration Driver.

Sequentially completes all 10 SWE-bench Lite sessions:
1. Monitors the in-flight Session 5 rescue pass (lite300-s5-rescue).
2. Merges newly rescued clean patches into results/lite300-s5/predictions.json.
3. Automatically commits and pushes Session 5 predictions to origin main.
4. Launches the full improvement loop across Sessions 6 through 10:
   - 3 diverse tournament candidates per instance.
   - AST static compilation gates on every candidate.
   - Automatic rescue pass on unpatched instances.
   - Synchronizes final predictions to origin main.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def is_process_running(keyword: str) -> bool:
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Get-CimInstance Win32_Process | Where-Object {{ $_.CommandLine -like '*{keyword}*' }} | Select-Object -Property ProcessId"],
            capture_output=True,
            text=True,
        )
        lines = [l.strip() for l in res.stdout.splitlines() if l.strip().isdigit()]
        # Exclude current process
        return len(lines) > 0
    except Exception:
        return False


def wait_for_s5_rescue() -> None:
    print("[orchestrator] Waiting for in-flight Session 5 rescue pass (lite300-s5-rescue) to complete...", flush=True)
    rescue_meta = ROOT / "results" / "lite300-s5-rescue" / "predictions.json"
    
    # Wait while the runner is active
    consecutive_done = 0
    while True:
        # Check if the runner process is still active
        running = is_process_running("lite300-s5-rescue")
        if not running:
            consecutive_done += 1
            if consecutive_done >= 2:
                print("\n[orchestrator] Session 5 rescue pass finished!", flush=True)
                break
        else:
            consecutive_done = 0
        
        # Print status
        patch_files = list((ROOT / "results" / "lite300-s5-rescue").glob("*/patch.diff")) if (ROOT / "results" / "lite300-s5-rescue").exists() else []
        print(f"[orchestrator] Waiting for rescue run... (completed instances so far: {len(patch_files)}/8)", flush=True)
        time.sleep(30)


def merge_and_push_s5() -> None:
    print("\n[orchestrator] Merging Session 5 rescue patches...", flush=True)
    source = ROOT / "results" / "lite300-s5-rescue"
    target = ROOT / "results" / "lite300-s5"
    if source.exists() and target.exists():
        subprocess.run([PYTHON, "scripts/merge_predictions.py", "--source", str(source), "--target", str(target)], cwd=str(ROOT))

    # Push to git
    try:
        subprocess.run(["git", "add", "results/lite300-s5/predictions.json"], cwd=str(ROOT))
        msg = "feat(bench): finalize Session 5 predictions post-rescue"
        res = subprocess.run(["git", "commit", "-m", msg], cwd=str(ROOT), capture_output=True, text=True)
        if res.returncode == 0:
            print("[orchestrator] Committed Session 5 predictions.", flush=True)
            subprocess.run(["git", "push", "origin", "main"], cwd=str(ROOT))
    except Exception as exc:
        print(f"[orchestrator] Git push notice: {exc}", flush=True)


def run_remaining_sessions() -> None:
    print("\n" + "=" * 70, flush=True)
    print("STARTING AUTONOMOUS BENCHMARK: SESSIONS 6 -> 10 (150 INSTANCES)", flush=True)
    print("=" * 70, flush=True)

    cmd = [
        PYTHON, "scripts/run_all_sessions.py",
        "--start", "6",
        "--end", "10",
        "--cooldown", "30",
    ]
    subprocess.run(cmd, cwd=str(ROOT))


def main() -> None:
    # 1. Complete Session 5
    wait_for_s5_rescue()
    merge_and_push_s5()

    # 2. Run Sessions 6 through 10 with full improvement loop
    run_remaining_sessions()
    print("\n[orchestrator] All 10 benchmark sessions completed!", flush=True)


if __name__ == "__main__":
    main()
