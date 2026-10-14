"""
Session 6 Improvement Tournament Runner (lite300-s6-v3).

Re-evaluates the 19 unpatched instances of Session 6 (Requests, Xarray, Pylint, Pytest)
using the 3-candidate tournament engine with 8 empirical invariants,
then merges clean AST patches into results/lite300-s6/predictions.json and pushes to origin main.
"""

import json
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

UNPATCHED_INSTANCES = [
    "psf__requests-2317", "psf__requests-2674", "psf__requests-3362",
    "pydata__xarray-3364", "pydata__xarray-4094", "pydata__xarray-4248", "pydata__xarray-5131",
    "pylint-dev__pylint-5859", "pylint-dev__pylint-7114", "pylint-dev__pylint-7228", "pylint-dev__pylint-7993",
    "pytest-dev__pytest-11148", "pytest-dev__pytest-5103", "pytest-dev__pytest-5221", "pytest-dev__pytest-5413",
    "pytest-dev__pytest-5692", "pytest-dev__pytest-7220", "pytest-dev__pytest-7373", "pytest-dev__pytest-7432",
]


def main() -> None:
    print("=" * 70, flush=True)
    print(f"LAUNCHING SESSION 6 FRESH TOURNAMENT IMPROVEMENT LOOP ({len(UNPATCHED_INSTANCES)} instances)", flush=True)
    print("=" * 70, flush=True)

    cmd = [
        PYTHON, "-m", "src.bench.runner",
        "--run-id", "lite300-s6-v3",
        "--instances", *UNPATCHED_INSTANCES,
        "--candidates", "3",
        "--workers", "1",
        "--timeout", "500",
        "--max-retries", "2",
    ]
    subprocess.run(cmd, cwd=str(ROOT))

    # Merge newly rescued clean patches into lite300-s6
    v3_dir = ROOT / "results" / "lite300-s6-v3"
    base_dir = ROOT / "results" / "lite300-s6"
    if v3_dir.exists():
        print("[s6-improvement] Merging fresh patches into results/lite300-s6/predictions.json...", flush=True)
        subprocess.run([
            PYTHON, "scripts/merge_predictions.py",
            "--source", str(v3_dir),
            "--target", str(base_dir),
        ], cwd=str(ROOT))

    # Commit and push
    try:
        subprocess.run(["git", "add", "results/lite300-s6/predictions.json"], cwd=str(ROOT))
        subprocess.run(["git", "commit", "-m", "feat(bench): update Session 6 predictions with tournament v3 patches"], cwd=str(ROOT))
        subprocess.run(["git", "push", "origin", "main"], cwd=str(ROOT))
    except Exception as exc:
        print(f"[s6-improvement] Git notice: {exc}", flush=True)

    print("\n[s6-improvement] Session 6 improvement loop complete!", flush=True)


if __name__ == "__main__":
    main()
