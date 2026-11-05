"""
Orchestrates sequential Docker evaluations across Wave B for Session 3 and Session 4.
Ensures single-worker isolation and automatic cleanup.
"""
import subprocess
import sys
import os

def run_cmd(cmd):
    print(f"\n>>> Running: {' '.join(cmd)}\n", flush=True)
    res = subprocess.run(cmd, cwd=os.getcwd())
    if res.returncode != 0:
        print(f"Command failed with code {res.returncode}", flush=True)
    return res.returncode

def main():
    print("=== STARTING WAVE B DOCKER EVALUATION ===", flush=True)

    # 1. Session 3 Batch
    s3_instances = [
        "django__django-13768",
        "django__django-13925",
        "django__django-13933",
        "django__django-14017",
    ]
    print(f"\n[1/2] Evaluating Session 3 Wave B: {s3_instances}", flush=True)
    cmd_s3 = [
        sys.executable, "-m", "src.bench.harness_eval",
        "--run-id", "lite300-s3",
        "--instances", *s3_instances,
        "--max-workers", "1"
    ]
    run_cmd(cmd_s3)

    # 2. Session 4 Batch
    s4_instances = [
        "django__django-15388",
        "django__django-15695",
    ]
    print(f"\n[2/2] Evaluating Session 4 Wave B: {s4_instances}", flush=True)
    cmd_s4 = [
        sys.executable, "-m", "src.bench.harness_eval",
        "--run-id", "lite300-s4",
        "--instances", *s4_instances,
        "--max-workers", "1"
    ]
    run_cmd(cmd_s4)

    print("\n=== WAVE B EVALUATION FINISHED ===", flush=True)

if __name__ == "__main__":
    main()
