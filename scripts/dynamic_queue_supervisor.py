"""
ISHA Dynamic Improvement Queue Supervisor.

Orchestrates multi-worker benchmark execution:
- Monitors currently running parallel sessions (5, 9, 10).
- As soon as ANY worker finishes, immediately assigns the next session from [6, 7, 8].
- For each assigned session:
  1. Runs 3-candidate tournament (--candidates 3) enforcing all 8 empirical invariants.
  2. Runs automatic rescue loop (-r2) on unpatched instances.
  3. Merges the best winning patches into results/lite300-s{N}/predictions.json.
  4. Commits and pushes predictions to origin main.
- Displays final SSOT audited scorecard once all sessions are complete.
"""

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

PENDING_QUEUE = [6, 7, 8]
QUEUE_LOCK = threading.Lock()
COMPLETED_SESSIONS = set()


def is_session_running(session_name: str) -> bool:
    """Check if a benchmark runner process is currently processing this session."""
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"Get-CimInstance Win32_Process | Where-Object {{ $_.CommandLine -like '*{session_name}*' }} | Select-Object -Property ProcessId"],
            capture_output=True,
            text=True,
        )
        lines = [l.strip() for l in res.stdout.splitlines() if l.strip().isdigit()]
        return len(lines) > 0
    except Exception:
        return False


def run_session_improvement_loop(session_num: int) -> None:
    session_name = f"lite300-s{session_num}"
    print(f"\n[supervisor] >>> WORKER CLAIMED SESSION {session_num} ({session_name}) <<<", flush=True)

    cmd = [
        PYTHON, "scripts/run_all_sessions.py",
        "--start", str(session_num),
        "--end", str(session_num),
        "--cooldown", "10",
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT))
    if proc.returncode == 0:
        print(f"[supervisor] Session {session_num} tournament & improvement loop completed successfully!", flush=True)
    else:
        print(f"[supervisor] Warning: Session {session_num} exited with code {proc.returncode}", flush=True)

    with QUEUE_LOCK:
        COMPLETED_SESSIONS.add(session_num)


def worker_thread(worker_id: int) -> None:
    """Worker pulls next session from queue and runs the improvement loop."""
    while True:
        target_session = None
        with QUEUE_LOCK:
            if PENDING_QUEUE:
                target_session = PENDING_QUEUE.pop(0)

        if target_session is None:
            print(f"[supervisor] Worker {worker_id}: No more sessions in queue. Exiting.", flush=True)
            break

        run_session_improvement_loop(target_session)


def main() -> None:
    print("=" * 70, flush=True)
    print("ISHA DYNAMIC WORKER QUEUE SUPERVISOR ACTIVE", flush=True)
    print("Pending Queue: Sessions 6 -> 7 -> 8", flush=True)
    print("Currently Monitoring Initial Parallel Sessions: 5, 9, 10", flush=True)
    print("=" * 70, flush=True)

    # Initial sessions being tracked
    initial_sessions = {5: "lite300-s5", 9: "lite300-s9", 10: "lite300-s10"}
    active_workers: list[threading.Thread] = []
    worker_counter = 1

    while PENDING_QUEUE or any(is_session_running(sname) for sname in initial_sessions.values()) or any(t.is_alive() for t in active_workers):
        # Check if an initial session has finished
        finished_initial = []
        for snum, sname in list(initial_sessions.items()):
            if not is_session_running(sname):
                # Ensure it has predictions or completed base
                pred_file = ROOT / "results" / sname / "predictions.json"
                if pred_file.is_file():
                    finished_initial.append(snum)

        for snum in finished_initial:
            sname = initial_sessions.pop(snum)
            print(f"\n[supervisor] Initial Session {snum} ({sname}) finished!", flush=True)
            # Immediately assign next session from queue to a new worker thread
            with QUEUE_LOCK:
                if PENDING_QUEUE:
                    next_s = PENDING_QUEUE.pop(0)
                    print(f"[supervisor] Dispatching next queued Session {next_s} to Worker {worker_counter}...", flush=True)
                    t = threading.Thread(target=run_session_improvement_loop, args=(next_s,), daemon=True)
                    t.start()
                    active_workers.append(t)
                    worker_counter += 1

        # Check alive workers count, clean up completed
        active_workers = [t for t in active_workers if t.is_alive()]

        # Sleep before next poll
        time.sleep(20)

    print("\n" + "=" * 70, flush=True)
    print("ALL SESSIONS (5, 6, 7, 8, 9, 10) FULLY COMPLETED!", flush=True)
    print("=" * 70, flush=True)

    # Print final scoreboard
    subprocess.run([PYTHON, "scripts/score.py"], cwd=str(ROOT))


if __name__ == "__main__":
    main()
