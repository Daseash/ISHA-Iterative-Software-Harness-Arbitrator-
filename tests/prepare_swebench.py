"""
ISHA SWE-bench checkout preparation — clones each fixture instance at its base commit.

Creates one checkout per instance under swebench_checkouts/<instance_id>,
which is where tests/swebench_runner.py --mode full expects to find them.

Usage:
    python tests/prepare_swebench.py             # all fixture instances
    python tests/prepare_swebench.py --limit 1   # first instance only
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "swebench_lite_sample.jsonl"
CHECKOUTS = ROOT / "swebench_checkouts"


def load_tasks(limit: int) -> list:
    if not FIXTURE.exists():
        raise SystemExit(f"fixture not found: {FIXTURE}")
    tasks = [json.loads(line) for line in FIXTURE.read_text(encoding="utf-8").splitlines() if line.strip()]
    return tasks[:limit]


def _run(cmd: list, cwd: Path | None = None, timeout: int = 900) -> str:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env={"GIT_TERMINAL_PROMPT": "0", "PATH": subprocess.os.environ["PATH"]},
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} -> {proc.stderr.strip()[:400]}")
    return proc.stdout.strip()


def prepare(task: dict) -> str:
    """Clone (or refresh) one instance checkout. Returns a status label."""
    dest = CHECKOUTS / task["instance_id"].replace("/", "__")
    repo = task["repo"]
    commit = task["base_commit"]
    url = f"https://github.com/{repo}.git"

    if (dest / ".git").is_dir():
        try:
            head = _run(["git", "rev-parse", "HEAD"], cwd=dest)
            if head == commit:
                return "up-to-date"
        except RuntimeError:
            pass
    else:
        dest.mkdir(parents=True, exist_ok=True)
        _run(["git", "init", "-q"], cwd=dest)

    try:
        _run(["git", "remote", "get-url", "origin"], cwd=dest)
    except RuntimeError:
        _run(["git", "remote", "add", "origin", url], cwd=dest)

    _run(["git", "config", "core.autocrlf", "false"], cwd=dest)
    _run(["git", "fetch", "--depth", "1", "origin", commit], cwd=dest, timeout=1800)
    _run(["git", "checkout", "-q", "--force", "FETCH_HEAD"], cwd=dest)
    return "cloned"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare SWE-bench checkouts for ISHA")
    parser.add_argument("--limit", type=int, default=3, help="Number of fixture instances")
    args = parser.parse_args()

    tasks = load_tasks(args.limit)
    print(f"Preparing {len(tasks)} checkout(s) under {CHECKOUTS}")
    failures = 0
    for task in tasks:
        try:
            status = prepare(task)
            print(f"  {task['instance_id']:<30} {status}")
        except Exception as exc:
            failures += 1
            print(f"  {task['instance_id']:<30} FAILED: {exc}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
