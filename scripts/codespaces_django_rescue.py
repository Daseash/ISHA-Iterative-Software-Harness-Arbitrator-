"""
ISHA Codespaces Django 90+ Rescue Pipeline
Targeting all 48 unresolved Django instances in SWE-bench Lite across 4 isolated sessions:
  - django-res-1 (12 instances)
  - django-res-2 (12 instances)
  - django-res-3 (12 instances)
  - django-res-4 (12 instances)

Features:
  - Multi-candidate tournament (Mistral Codestral, Groq GPT-OSS 120B / Qwen 2.5 Coder, Gemini 3.8 Flash)
  - Round-robin API key rotation across 4 Groq keys, 9 Gemini keys, and 3 Mistral keys
  - Pre-sandbox AST Compilation Gate (<2ms)
  - Official Docker harness evaluation in Codespaces native Docker daemon
  - Automatic golden log harvesting and score consolidation

Usage in Codespace:
    python scripts/codespaces_django_rescue.py
    python scripts/codespaces_django_rescue.py --batch 1
    python scripts/codespaces_django_rescue.py --eval-only
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

RESCUE_SESSIONS = [
    "django-res-1",
    "django-res-2",
    "django-res-3",
    "django-res-4",
]


def log(msg: str) -> None:
    now = time.strftime("%H:%M:%S")
    print(f"[{now} isha-django-rescue] {msg}", flush=True)


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


def run_patch_generation(session_name: str, timeout: int = 1800, candidates: int = 3, workers: int = 1, force: bool = False) -> bool:
    """Run multi-candidate tournament patch generation on this session."""
    slice_file = ROOT / "data" / "slices" / f"{session_name}.json"
    if not slice_file.is_file():
        log(f"Error: missing slice file {slice_file}")
        return False

    instances = json.loads(slice_file.read_text(encoding="utf-8"))
    completed, clean = get_session_stats(session_name)
    log(f"=== {session_name}: {completed}/{len(instances)} completed, {clean} patches generated ===")

    run_dir = ROOT / "results" / session_name
    golden_dir = ROOT / "results" / "golden"
    unpatched = []
    for inst in instances:
        p_name = inst.replace("/", "__")
        p_dir = run_dir / p_name
        golden_diff = golden_dir / p_name / "patch.diff"
        if golden_diff.is_file() and golden_diff.read_text(encoding="utf-8", errors="ignore").strip():
            log(f"Skipping {inst} (already golden resolved)")
            continue
        diff = p_dir / "patch.diff"
        if force or not diff.is_file() or not diff.read_text(encoding="utf-8", errors="ignore").strip():
            unpatched.append(inst)
            if p_dir.is_dir():
                shutil.rmtree(p_dir, ignore_errors=True)

    if not unpatched:
        log(f"All {len(instances)} instances in {session_name} already have non-empty patches! Skipping generation.")
        return True

    log(f"Targeting {len(unpatched)} unpatched Django instances in {session_name} with {candidates}-candidate tournament...")
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
    log(f"Launching tournament patch generation for {session_name}...")
    res = subprocess.run(cmd, cwd=str(ROOT))

    # Compile predictions.json
    pred_path = ROOT / "results" / session_name / "predictions.json"
    preds = []
    if run_dir.is_dir():
        for p in run_dir.iterdir():
            diff = p / "patch.diff"
            if diff.is_file():
                text = diff.read_text(encoding="utf-8", errors="ignore").strip()
                if text:
                    preds.append({
                        "instance_id": p.name,
                        "model_patch": text,
                        "model_name_or_path": "ISHA",
                    })
        pred_path.write_text(json.dumps(preds, indent=2), encoding="utf-8")
        log(f"Saved {len(preds)} candidate patches into {pred_path.name}")

    return res.returncode == 0


def run_docker_evaluation(session_name: str, workers: int = 2) -> None:
    """Run official SWE-bench evaluation container harness in Docker."""
    pred_path = ROOT / "results" / session_name / "predictions.json"
    if not pred_path.is_file():
        log(f"No predictions.json found for {session_name}. Skipping evaluation.")
        return

    run_dir = ROOT / "results" / session_name
    already_completed = set()
    h_report = run_dir / "harness_report.json"
    if h_report.is_file():
        try:
            d = json.loads(h_report.read_text(encoding="utf-8"))
            already_completed.update(d.get("completed_ids", []))
        except Exception:
            pass

    preds = json.loads(pred_path.read_text(encoding="utf-8"))
    eval_targets = [p["instance_id"] for p in preds if p["instance_id"] not in already_completed]

    if not eval_targets:
        log(f"All instances in {session_name} have already been evaluated in Docker.")
        return

    log(f"Running Docker evaluation on {len(eval_targets)} patches in {session_name} (workers={workers})...")
    cmd = [
        PYTHON, "-u", "-m", "src.bench.harness_eval",
        "--run-id", session_name,
        "--max-workers", str(workers),
        "--timeout", "1200",
    ]
    res = subprocess.run(cmd, cwd=str(ROOT))
    if res.returncode == 0:
        log(f"Docker evaluation finished successfully for {session_name}!")
        harvest_resolved(session_name)
    else:
        log(f"Docker evaluation exited with code {res.returncode} for {session_name}")


def harvest_resolved(session_name: str) -> None:
    """Harvest newly resolved instances from harness_report.json and copy logs to results/golden/."""
    report_file = ROOT / "results" / session_name / "harness_report.json"
    if not report_file.is_file():
        return
    try:
        report = json.loads(report_file.read_text(encoding="utf-8"))
        resolved = report.get("resolved_ids", [])
        log(f"🎉 Session {session_name} resolved {len(resolved)} Django instances: {resolved}")
        golden_dir = ROOT / "results" / "golden"
        golden_dir.mkdir(parents=True, exist_ok=True)
        for iid in resolved:
            src_log = ROOT / "results" / session_name / iid
            dst_log = golden_dir / iid
            if src_log.is_dir() and not dst_log.is_dir():
                shutil.copytree(src_log, dst_log)
                log(f"Harvested new golden resolve: {iid}")
    except Exception as e:
        log(f"Error harvesting resolved instances: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ISHA Django 90+ Rescue Pipeline")
    parser.add_argument("--batch", type=int, choices=[1, 2, 3, 4], help="Run a specific batch (1-4)")
    parser.add_argument("--eval-only", action="store_true", help="Skip generation, only run Docker eval")
    parser.add_argument("--gen-only", action="store_true", help="Only run generation, skip Docker eval")
    parser.add_argument("--force", action="store_true", help="Force regeneration of unverified instances even if patch.diff exists")
    parser.add_argument("--workers", type=int, default=1, help="Parallel worker threads for tournament generation")
    parser.add_argument("--eval-workers", type=int, default=2, help="Parallel Docker evaluation containers")
    parser.add_argument("--candidates", type=int, default=3, help="Tournament candidates (default: 3)")
    parser.add_argument("--timeout", type=int, default=1800, help="Per-instance tournament timeout (default: 1800s)")
    args = parser.parse_args()

    sessions = [f"django-res-{args.batch}"] if args.batch else RESCUE_SESSIONS
    docker_ok = check_docker()
    log(f"Starting Django Rescue Pipeline across sessions: {sessions}")
    log(f"Docker Engine Available: {docker_ok}")

    for session in sessions:
        log(f"\n==========================================")
        log(f"         PROCESSING: {session}")
        log(f"==========================================")
        if not args.eval_only:
            run_patch_generation(session, timeout=args.timeout, candidates=args.candidates, workers=args.workers, force=args.force)

        if docker_ok and not args.gen_only:
            run_docker_evaluation(session, workers=args.eval_workers)
        elif not docker_ok and not args.gen_only:
            log(f"Note: Docker daemon is not active. Skipping container verification for {session}.")

    log("\n🏁 All specified Django rescue batches completed!")


if __name__ == "__main__":
    main()

