"""
ISHA Fast Multi-Session Pipeline Orchestrator

Applies the high-yield, fast patch generation strategy across all sessions:
- Flags: --candidates 3 --no-verify --workers 1 --timeout 300
- Workflow:
  1. Complete Session 9 (finish remaining instances).
  2. Complete Session 10 (finish remaining instances).
  3. Run Session 5.
  4. Run Session 6.
  5. Run Session 7.
  6. Run Session 8.
  7. Run official Docker harness evaluation (harness_eval) across all sessions.
  8. Run score.py and sync MAKING_BETTER.md.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
LOG_DIR = Path(r"C:\Users\Eashwar\AppData\Local\Temp\opencode")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    now = time.strftime("%H:%M:%S")
    print(f"[{now} master-fast] {msg}", flush=True)


def get_session_stats(session_name: str) -> tuple[int, int]:
    """Returns (completed_instances, clean_patches)."""
    run_dir = ROOT / "results" / session_name
    if not run_dir.is_dir():
        return 0, 0
    completed = 0
    clean = 0
    for p in run_dir.iterdir():
        if p.is_dir():
            meta = p / "meta.json"
            diff = p / "patch.diff"
            if meta.is_file():
                completed += 1
                if diff.is_file() and diff.read_text(encoding="utf-8", errors="ignore").strip():
                    clean += 1
    return completed, clean


def clean_incomplete_dirs(session_name: str) -> None:
    """Only remove directories that do not have meta.json (interrupted instances)."""
    run_dir = ROOT / "results" / session_name
    if not run_dir.is_dir():
        return
    for p in run_dir.iterdir():
        if p.is_dir():
            meta = p / "meta.json"
            if not meta.is_file():
                try:
                    shutil.rmtree(p)
                    log(f"Cleaned incomplete dir {p.name} in {session_name}")
                except Exception as e:
                    log(f"Warning: could not clean {p.name}: {e}")


def run_session(session_name: str) -> bool:
    slice_file = ROOT / "data" / "slices" / f"{session_name}.json"
    if not slice_file.is_file():
        log(f"Error: missing slice file {slice_file}")
        return False
    instances = json.loads(slice_file.read_text(encoding="utf-8"))
    
    clean_incomplete_dirs(session_name)
    completed, clean = get_session_stats(session_name)
    log(f"=== {session_name}: {completed}/{len(instances)} completed, {clean} clean patches locked ===")
    
    if completed >= len(instances):
        log(f"{session_name} is already complete! Skipping runner.")
        return True
    
    out_log = open(LOG_DIR / f"{session_name}_stdout.log", "a", encoding="utf-8")
    err_log = open(LOG_DIR / f"{session_name}_stderr.log", "a", encoding="utf-8")
    
    cmd = [
        PYTHON, "-u", "-m", "src.bench.runner",
        "--run-id", session_name,
        "--candidates", "3",
        "--workers", "1",
        "--no-verify",
        "--timeout", "300",
        "--instances", *instances,
    ]
    log(f"Launching {session_name} runner (timeout=300s, candidates=3, no-verify)...")
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=out_log,
        stderr=err_log,
    )
    rc = proc.wait()
    out_log.close()
    err_log.close()
    
    completed_after, clean_after = get_session_stats(session_name)
    log(f"Session {session_name} runner exited with code {rc}. Final count: {completed_after}/{len(instances)} done, {clean_after} patches.")
    return rc == 0


def run_docker_eval(session_name: str) -> None:
    pred_file = ROOT / "results" / session_name / "predictions.json"
    if not pred_file.is_file():
        log(f"No predictions.json for {session_name}, skipping harness eval.")
        return
    log(f"Running official Docker evaluation for {session_name}...")
    cmd = [PYTHON, "-m", "src.bench.harness_eval", "--run-id", session_name, "--max-workers", "1"]
    subprocess.run(cmd, cwd=str(ROOT))


def main() -> None:
    log("Starting ISHA Fast Multi-Session Pipeline...")
    sessions = [
        "lite300-s9",
        "lite300-s10",
        "lite300-s5",
        "lite300-s6",
        "lite300-s7",
        "lite300-s8",
    ]
    
    for s in sessions:
        log(f"\n>>> PROCESSING SESSION: {s} <<<")
        success = run_session(s)
        if not success:
            log(f"Warning: session {s} reported non-zero exit, continuing to next...")
    
    log("\nAll candidate patch generation sessions finished!")
    
    # Check if Docker is available
    try:
        docker_check = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
        docker_available = (docker_check.returncode == 0)
    except Exception:
        docker_available = False
    
    if docker_available:
        log("Docker detected! Running official harness evaluation across all sessions...")
        for s in sessions:
            run_docker_eval(s)
    else:
        log("Docker not reachable. Skipping in-container harness evaluation for now.")
    
    # Update scores
    log("Updating scoreboard and sync...")
    score_script = ROOT / "scripts" / "score.py"
    if score_script.is_file():
        subprocess.run([PYTHON, str(score_script)], cwd=str(ROOT))
    sync_script = ROOT / "scripts" / "sync_making_better.py"
    if sync_script.is_file():
        subprocess.run([PYTHON, str(sync_script)], cwd=str(ROOT))
    
    log("Pipeline complete!")


if __name__ == "__main__":
    main()
