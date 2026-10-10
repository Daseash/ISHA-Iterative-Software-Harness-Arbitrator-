"""
ISHA Autonomous Benchmark Pipeline: Sessions 5 through 10

Runs SWE-bench Lite benchmark sessions sequentially:
1. Executes base 30-instance run with 3 diverse tournament candidates.
2. Identifies any unpatched/failed instances.
3. Automatically triggers an improvement/rescue pass with fresh seeds.
4. Merges rescued patches into predictions.json.
5. Pushes predictions to GitHub origin main.
6. Progresses through all remaining sessions to reach all 300 instances.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_cmd(cmd: list[str]) -> int:
    print(f"\n[pipeline] Running: {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=str(ROOT))
    return proc.returncode


def get_patch_stats(predictions_file: Path) -> tuple[int, int, list[str]]:
    """Return (total_count, non_empty_count, list_of_unpatched_ids)."""
    if not predictions_file.is_file():
        return 0, 0, []
    try:
        preds = json.loads(predictions_file.read_text(encoding="utf-8"))
        non_empty = [p for p in preds if p.get("model_patch", "").strip()]
        unpatched = [p["instance_id"] for p in preds if not p.get("model_patch", "").strip()]
        return len(preds), len(non_empty), unpatched
    except Exception as exc:
        print(f"[pipeline] Error reading {predictions_file}: {exc}")
        return 0, 0, []


def git_push_predictions(session_name: str) -> None:
    """Stage and push session predictions to GitHub, keeping plan.md strictly local."""
    try:
        pred_path = f"results/{session_name}/predictions.json"
        slice_path = f"data/slices/{session_name}.json"
        subprocess.run(["git", "add", pred_path, slice_path], cwd=str(ROOT), check=False)
        msg = f"feat(bench): finalize {session_name} predictions"
        res = subprocess.run(["git", "commit", "-m", msg], cwd=str(ROOT), capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[pipeline] Committed {session_name} predictions.")
            push_res = subprocess.run(["git", "push", "origin", "main"], cwd=str(ROOT), capture_output=True, text=True)
            if push_res.returncode == 0:
                print(f"[pipeline] Successfully pushed {session_name} to origin main.")
            else:
                print(f"[pipeline] Warning: git push returned {push_res.returncode}: {push_res.stderr}")
    except Exception as exc:
        print(f"[pipeline] Git commit/push error: {exc}")


def run_session(session_num: int) -> None:
    session_name = f"lite300-s{session_num}"
    slice_file = ROOT / "data" / "slices" / f"{session_name}.json"
    pred_file = ROOT / "results" / session_name / "predictions.json"

    print("\n" + "=" * 70, flush=True)
    print(f"  STARTING SESSION {session_num}: {session_name} (30 instances)", flush=True)
    print("=" * 70, flush=True)

    if not slice_file.is_file():
        print(f"[pipeline] Error: Slice file {slice_file} not found! Skipping.", flush=True)
        return

    instances = json.loads(slice_file.read_text(encoding="utf-8"))
    total, non_empty, unpatched = get_patch_stats(pred_file)
    if total >= len(instances) and non_empty >= int(len(instances) * 0.9):
        print(f"[pipeline] {session_name} already has {non_empty}/{total} clean patches. Skipping base run.", flush=True)
    else:
        print(f"[pipeline] Launching base runner for {session_name} ({len(instances)} instances)...", flush=True)
        cmd = [
            PYTHON, "-m", "src.bench.runner",
            "--run-id", session_name,
            "--instances", *instances,
            "--candidates", "3",
            "--workers", "1",
            "--timeout", "500",
            "--max-retries", "2",
        ]
        rc = run_cmd(cmd)
        if rc != 0:
            print(f"[pipeline] Warning: Base run for {session_name} exited with code {rc}.", flush=True)

    # 2. Check Results & Identify Unpatched Instances
    total, non_empty, unpatched = get_patch_stats(pred_file)
    yield_pct = (non_empty / total * 100) if total > 0 else 0.0
    print(f"\n[pipeline] {session_name} Base Yield: {non_empty}/{total} ({yield_pct:.1f}%)", flush=True)

    # 3. Rescue Pass if < 95% (and unpatched instances exist)
    if unpatched and len(unpatched) > 0 and yield_pct < 95.0:
        print(f"\n[pipeline] Launching rescue loop for {len(unpatched)} unpatched instances in {session_name}:", flush=True)
        for u in unpatched:
            print(f"  - {u}")

        rescue_run_id = f"{session_name}-r2"
        rescue_slice = ROOT / "data" / "slices" / f"{session_name}-rescue.json"
        rescue_slice.write_text(json.dumps(unpatched, indent=2), encoding="utf-8")

        rescue_cmd = [
            PYTHON, "-m", "src.bench.runner",
            "--run-id", rescue_run_id,
            "--instances", *unpatched,
            "--candidates", "3",
            "--workers", "1",
            "--timeout", "500",
            "--max-retries", "2",
        ]
        run_cmd(rescue_cmd)

        # Merge rescued patches into base predictions
        merge_cmd = [
            PYTHON, "scripts/merge_predictions.py",
            "--source", f"results/{rescue_run_id}",
            "--target", f"results/{session_name}",
        ]
        run_cmd(merge_cmd)

        # Re-check stats
        total, non_empty, unpatched = get_patch_stats(pred_file)
        yield_pct = (non_empty / total * 100) if total > 0 else 0.0
        print(f"\n[pipeline] {session_name} Final Post-Rescue Yield: {non_empty}/{total} ({yield_pct:.1f}%)", flush=True)

    # 4. Commit and Push
    git_push_predictions(session_name)
    print(f"[pipeline] Session {session_num} complete! Clean patches locked: {non_empty}/{total}.", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run autonomous benchmark across Lite 300 sessions")
    parser.add_argument("--start", type=int, default=5, help="Starting session number (e.g. 5)")
    parser.add_argument("--end", type=int, default=10, help="Ending session number (e.g. 10)")
    parser.add_argument("--cooldown", type=int, default=60, help="Cooldown in seconds between sessions")
    args = parser.parse_args()

    print("=" * 70, flush=True)
    print(f"ISHA AUTONOMOUS ALL-SESSIONS PIPELINE: SESSIONS {args.start} -> {args.end}", flush=True)
    print("=" * 70, flush=True)

    for s in range(args.start, args.end + 1):
        run_session(s)
        if s < args.end:
            print(f"\n[pipeline] Cooldown: waiting {args.cooldown}s before starting Session {s + 1}...", flush=True)
            time.sleep(args.cooldown)

    print("\n" + "=" * 70, flush=True)
    print("ALL REQUESTED SESSIONS COMPLETED SUCCESSFULLY!", flush=True)
    print("=" * 70, flush=True)


if __name__ == "__main__":
    main()
