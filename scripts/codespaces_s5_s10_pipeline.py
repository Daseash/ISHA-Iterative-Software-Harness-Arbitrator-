"""
ISHA Codespaces S5 to S10 Pipeline — Patch Generation & Official Docker Evaluation

Runs the best improvement loop across Sessions 5 through 10:
  1. 3-Candidate Tournament (--candidates 3) across diverse strategies
     (minimal_diff, root_cause_first, call_site_aware).
  2. AST static compiler gates + in-loop feedback repair.
  3. Official Docker harness evaluation in Codespace's native Docker engine.
  4. Automatic scoreboard calculation via scripts/score.py.

Usage in Codespace:
    python scripts/codespaces_s5_s10_pipeline.py
    python scripts/codespaces_s5_s10_pipeline.py --sessions lite300-s5 lite300-s6
    python scripts/codespaces_s5_s10_pipeline.py --eval-only
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
LOG_DIR = Path(tempfile.gettempdir()) / "isha_pipeline_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

TARGET_SESSIONS = [
    "lite300-s5",
    "lite300-s6",
    "lite300-s7",
    "lite300-s8",
    "lite300-s9",
    "lite300-s10",
]


def log(msg: str) -> None:
    now = time.strftime("%H:%M:%S")
    print(f"[{now} isha-codespace] {msg}", flush=True)


def check_docker() -> bool:
    """Verify if Docker daemon is running."""
    try:
        res = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
        return res.returncode == 0
    except Exception:
        return False


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


def run_patch_generation(session_name: str, timeout: int = 360, candidates: int = 3, workers: int = 1) -> bool:
    """Run 3-candidate tournament patch generation with improvement loop."""
    slice_file = ROOT / "data" / "slices" / f"{session_name}.json"
    if not slice_file.is_file():
        log(f"Error: missing slice file {slice_file}")
        return False

    instances = json.loads(slice_file.read_text(encoding="utf-8"))
    completed, clean = get_session_stats(session_name)
    log(f"=== {session_name}: {completed}/{len(instances)} completed, {clean} patches generated ===")

    # Smart targeting: identify instances missing or with empty patches
    run_dir = ROOT / "results" / session_name
    unpatched = []
    for inst in instances:
        p_dir = run_dir / inst.replace("/", "__")
        diff = p_dir / "patch.diff"
        if not diff.is_file() or not diff.read_text(encoding="utf-8", errors="ignore").strip():
            unpatched.append(inst)
            if p_dir.is_dir():
                shutil.rmtree(p_dir, ignore_errors=True)

    if not unpatched:
        log(f"All {len(instances)} instances in {session_name} already have non-empty patches! Skipping patch generation.")
        return True

    log(f"Targeting {len(unpatched)} unpatched instances in {session_name} with 3-candidate tournament (workers={workers})...")
    cmd = [
        PYTHON, "-u", "-m", "src.bench.runner",
        "--run-id", session_name,
        "--candidates", str(candidates),
        "--workers", str(workers),
        "--no-verify",
        "--timeout", str(timeout),
        "--max-retries", "2",
        "--instances", *unpatched,
    ]
    log(f"Launching patch generator for {session_name} (candidates={candidates}, timeout={timeout}s)...")
    res = subprocess.run(cmd, cwd=str(ROOT))
    
    # Regenerate predictions.json to ensure all patches are synced
    pred_path = ROOT / "results" / session_name / "predictions.json"
    preds = {}
    run_dir = ROOT / "results" / session_name
    if run_dir.is_dir():
        for p in run_dir.iterdir():
            diff = p / "patch.diff"
            if diff.is_file():
                text = diff.read_text(encoding="utf-8", errors="ignore").strip()
                if text:
                    preds[p.name.replace("__", "/")] = text
        pred_path.write_text(json.dumps(preds, indent=2), encoding="utf-8")
        log(f"Synced {len(preds)} patches into {pred_path.name}")

    return res.returncode == 0


def run_docker_evaluation(session_name: str, workers: int = 2) -> None:
    """Run official SWE-bench evaluation container harness."""
    pred_path = ROOT / "results" / session_name / "predictions.json"
    if not pred_path.is_file():
        log(f"No predictions.json found for {session_name}. Skipping evaluation.")
        return

    log(f"Starting official Docker harness evaluation for {session_name} (workers={workers})...")
    cmd = [
        PYTHON, "-m", "src.bench.harness_eval",
        "--run-id", session_name,
        "--max-workers", str(workers),
    ]
    subprocess.run(cmd, cwd=str(ROOT))
    log(f"Docker evaluation complete for {session_name}!")


def main() -> None:
    parser = argparse.ArgumentParser(description="ISHA Codespaces S5-S10 Benchmark Pipeline")
    parser.add_argument("--sessions", nargs="+", default=TARGET_SESSIONS, help="Sessions to process")
    parser.add_argument("--timeout", type=int, default=360, help="Per-instance timeout in seconds")
    parser.add_argument("--candidates", type=int, default=3, help="Tournament candidates (default: 3)")
    parser.add_argument("--eval-workers", type=int, default=2, help="Parallel Docker eval containers (default: 2)")
    parser.add_argument("--gen-workers", type=int, default=1, help="Parallel patch generation workers (default: 1)")
    parser.add_argument("--eval-only", action="store_true", help="Skip patch generation and run Docker eval only")
    parser.add_argument("--skip-eval", action="store_true", help="Skip Docker eval and generate patches only")
    args = parser.parse_args()

    log("=" * 65)
    log("  ISHA CODESPACES BENCHMARK PIPELINE (S5 - S10)")
    log("=" * 65)
    log(f"Target sessions: {args.sessions}")
    log(f"Candidates per instance: {args.candidates}")
    log(f"Generation workers: {args.gen_workers}")

    docker_ok = check_docker()
    if docker_ok:
        log("Docker Engine: CONNECTED & READY")
    else:
        log("Docker Engine: NOT DETECTED (Docker eval will be skipped if requested)")

    # Step 1: Run Patch Generation & Evaluation for each session
    for session in args.sessions:
        log("\n" + "=" * 65)
        log(f"  PROCESSING SESSION: {session}")
        log("=" * 65)

        if not args.eval_only:
            run_patch_generation(session, timeout=args.timeout, candidates=args.candidates, workers=args.gen_workers)

        if not args.skip_eval and docker_ok:
            run_docker_evaluation(session, workers=args.eval_workers)
        elif not docker_ok and not args.skip_eval:
            log(f"Skipping Docker evaluation for {session} (Docker not running).")

    # Step 2: Show final updated scoreboard
    log("\n" + "=" * 65)
    log("  GENERATING AUDITED SCORECARD")
    log("=" * 65)
    score_script = ROOT / "scripts" / "score.py"
    if score_script.is_file():
        subprocess.run([PYTHON, str(score_script)], cwd=str(ROOT))

    log("\nCodespaces Pipeline Finished Successfully!")


if __name__ == "__main__":
    main()
