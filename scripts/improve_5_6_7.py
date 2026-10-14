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

SESSIONS = {
    "lite300-s5": [
        "matplotlib__matplotlib-22835",
        "matplotlib__matplotlib-24265",
        "matplotlib__matplotlib-25442",
        "mwaskom__seaborn-2848",
        "pallets__flask-4045",
        "pallets__flask-5063",
    ],
    "lite300-s6": [
        "psf__requests-2674",
        "pydata__xarray-4094",
        "pylint-dev__pylint-5859",
        "pylint-dev__pylint-7993",
        "pytest-dev__pytest-11148",
        "pytest-dev__pytest-5221",
        "pytest-dev__pytest-5413",
        "pytest-dev__pytest-5692",
        "pytest-dev__pytest-7220",
        "pytest-dev__pytest-7373",
    ],
    "lite300-s7": [
        "pytest-dev__pytest-9359",
        "scikit-learn__scikit-learn-10297",
        "scikit-learn__scikit-learn-10949",
        "scikit-learn__scikit-learn-11281",
        "scikit-learn__scikit-learn-12471",
        "scikit-learn__scikit-learn-13584",
        "scikit-learn__scikit-learn-25500",
        "scikit-learn__scikit-learn-25570",
        "scikit-learn__scikit-learn-25638",
        "scikit-learn__scikit-learn-25747",
        "sphinx-doc__sphinx-10325",
        "sphinx-doc__sphinx-10451",
        "sphinx-doc__sphinx-11445",
    ],
}


def run_batch(session_id: str, instances: list[str]) -> None:
    run_id = f"{session_id}-rescue-v4"
    print("=" * 72, flush=True)
    print(f"[{session_id}] LAUNCHING TOURNAMENT ON {len(instances)} UNPATCHED INSTANCES", flush=True)
    print("=" * 72, flush=True)

    cmd = [
        PYTHON, "-m", "src.bench.runner",
        "--run-id", run_id,
        "--instances", *instances,
        "--candidates", "3",
        "--workers", "1",
        "--timeout", "480",
        "--max-retries", "2",
    ]
    subprocess.run(cmd, cwd=str(ROOT))

    # Merge newly rescued clean patches
    source_dir = ROOT / "results" / run_id
    target_dir = ROOT / "results" / session_id
    if source_dir.exists():
        print(f"[{session_id}] Merging fresh patches into results/{session_id}/predictions.json...", flush=True)
        subprocess.run([
            PYTHON, "scripts/merge_predictions.py",
            "--source", str(source_dir),
            "--target", str(target_dir),
        ], cwd=str(ROOT))

    # Git commit and push
    pred_path = target_dir / "predictions.json"
    if pred_path.exists():
        try:
            subprocess.run(["git", "add", f"results/{session_id}/predictions.json"], cwd=str(ROOT))
            msg = f"feat(bench): update {session_id} predictions with rescue tournament patches"
            res = subprocess.run(["git", "commit", "-m", msg], cwd=str(ROOT), capture_output=True, text=True)
            if res.returncode == 0:
                print(f"[{session_id}] Committed predictions update.", flush=True)
                push_res = subprocess.run(["git", "push", "origin", "main"], cwd=str(ROOT), capture_output=True, text=True)
                if push_res.returncode == 0:
                    print(f"[{session_id}] Pushed to origin main successfully.", flush=True)
                else:
                    print(f"[{session_id}] Git push warning: {push_res.stderr}", flush=True)
        except Exception as exc:
            print(f"[{session_id}] Git push error: {exc}", flush=True)


def main() -> None:
    for session_id, instances in SESSIONS.items():
        run_batch(session_id, instances)

    print("\n" + "=" * 72, flush=True)
    print("ALL SESSIONS 5, 6, 7 RESCUE PASSES COMPLETE!", flush=True)
    print("=" * 72, flush=True)


if __name__ == "__main__":
    main()
