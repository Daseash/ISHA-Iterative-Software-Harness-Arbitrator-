"""
ISHA SWE-bench Harness Evaluation — thin, faithful wrapper around the
**official** swebench Docker harness.

Nothing here re-implements grading: the container images, the FAIL_TO_PASS /
PASS_TO_PASS lists and the per-repo log parsers all come from the official
package.  This module only

  * writes the predictions file the harness expects,
  * runs ``swebench.harness.run_evaluation`` with logs confined to the run
    directory, and
  * reads back the official report.

Windows note
------------
The harness itself is pure Python + the Docker API, so it runs from Windows
PowerShell against Docker Desktop's Linux engine.  WSL2 is the supported
backend for Docker Desktop (Settings -> General -> use WSL2).  If you prefer
to drive everything from a Linux shell, the same commands work inside WSL2:

    wsl -d Ubuntu -- bash -lc "cd /mnt/c/Users/Eashwar/ISHA/isha-agent && \\
        python -m src.bench.harness_eval --run-id baseline"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bench import dataset as ds  # noqa: E402

RESULTS_DIR = ROOT / "results"

# Files swebench materialises and then copies into the eval container.  On
# Windows ``Path.write_text`` turns every ``\n`` into ``\r\n``; bash dies on the
# CRs in ``/eval.sh`` (``set: pipefail\r: invalid option name``) and git apply
# dies on them in ``/tmp/patch.diff`` (``Stripping trailing CRs from patch``).
_CONTAINER_SUFFIXES = {".sh", ".diff", ".patch"}

_write_text_lf_installed = False


def install_lf_writes() -> None:
    """Force LF line endings for the files swebench ships into containers."""
    global _write_text_lf_installed
    if _write_text_lf_installed:
        return
    original = Path.write_text

    def write_text(self, data, *args, **kwargs):  # type: ignore[no-untyped-def]
        if self.suffix in _CONTAINER_SUFFIXES:
            kwargs.setdefault("newline", "\n")
        # swebench writes eval.sh / patch files without an explicit encoding;
        # on Windows that falls back to the cp1252 locale codec and crashes
        # with UnicodeEncodeError the moment a test spec contains any
        # non-ASCII character.  Force UTF-8 for everything the harness writes.
        kwargs.setdefault("encoding", "utf-8")
        return original(self, data, *args, **kwargs)

    Path.write_text = write_text  # type: ignore[method-assign]
    _write_text_lf_installed = True


def cleanup_images(prefix: str = "swebench/sweb.eval.") -> list[str]:
    """Drop eval images after a run — one per instance, ~4GB each."""
    import subprocess

    try:
        out = subprocess.run(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
            capture_output=True, text=True, timeout=60,
        )
        if out.returncode != 0:
            return []
        names = [n for n in out.stdout.split() if n.startswith(prefix)]
        for name in names:
            subprocess.run(
                ["docker", "rmi", "-f", name],
                capture_output=True, text=True, timeout=300,
            )
        return names
    except Exception:
        return []


def _predictions(run_dir: Path) -> Path:
    path = run_dir / "predictions.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} not found — run `python -m src.bench.runner --run-id "
            f"{run_dir.name}` first."
        )
    return path


def evaluate(
    run_dir: Path,
    max_workers: int = 3,
    timeout: int = 1800,
    run_eval_id: str | None = None,
    keep_images: bool = False,
) -> dict:
    """Run the official harness over a run's predictions and return its report."""
    ready, message = is_docker_ready()
    if not ready:
        raise RuntimeError(message)

    from swebench.harness.run_evaluation import main as swe_main

    install_lf_writes()

    predictions_path = _predictions(run_dir)
    preds = json.loads(predictions_path.read_text(encoding="utf-8"))
    instance_ids = [p["instance_id"] for p in preds if p.get("model_patch")]
    if not instance_ids:
        report = _empty_report(len(preds))
        _write_report(run_dir, report)
        return report

    eval_id = run_eval_id or run_dir.name
    report_dir = run_dir / "harness"
    report_dir.mkdir(parents=True, exist_ok=True)

    cwd = Path.cwd()
    log_root = run_dir / "harness"
    log_root.mkdir(parents=True, exist_ok=True)
    # The harness resolves logs/run_evaluation relative to the CWD, so run it
    # from the run directory: logs stay next to the results they explain.
    os.chdir(run_dir)
    try:
        swe_main(
            dataset_name=ds.DATASET_NAME,
            split=ds.SPLIT,
            instance_ids=instance_ids,
            predictions_path=str(predictions_path),
            max_workers=max_workers,
            open_file_limit=4096,
            run_id=eval_id,
            timeout=timeout,
            rewrite_reports=False,
            modal=False,
            report_dir=str(report_dir),
            task_repo=None,
        )
    finally:
        os.chdir(cwd)

    if not keep_images:
        removed = cleanup_images()
        if removed:
            print(f"Removed {len(removed)} eval image(s) to keep the disk free")

    return load_official_report(run_dir, eval_id)


def _empty_report(total: int) -> dict:
    return {
        "total_instances": total,
        "resolved_instances": 0,
        "resolved_ids": [],
        "note": "no non-empty model_patch was produced",
    }


def _write_report(run_dir: Path, report: dict) -> Path:
    out = run_dir / "harness_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out


def load_official_report(run_dir: Path, eval_id: str | None = None) -> dict:
    """Read back the harness report for a run (newest if not specified)."""
    report_dir = run_dir / "harness"
    candidates = sorted(report_dir.glob("*.json")) if report_dir.is_dir() else []
    # Prefer a run report over run.json metadata.
    scored = []
    for path in candidates:
        if path.name in ("run.json", "harness_report.json"):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if "resolved_ids" in payload:
            scored.append((0 if (eval_id and eval_id in path.name) else 1, path.name, payload))
    if not scored:
        return {}
    scored.sort(key=lambda t: (t[0], t[1]))
    report = scored[0][2]
    _write_report(run_dir, report)
    return report


def is_docker_ready() -> tuple[bool, str]:
    """(reachable, message) for the Docker daemon the harness needs."""
    try:
        import docker

        client = docker.from_env(timeout=10)
        version = client.version().get("Version", "unknown")
        return True, f"Docker {version} reachable"
    except Exception as exc:
        return False, (
            f"Docker daemon unreachable ({exc.__class__.__name__}: {exc}). "
            "Start Docker Desktop (WSL2 backend) and retry."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the official SWE-bench harness")
    parser.add_argument("--run-id", required=True, help="results/<run-id> to evaluate")
    parser.add_argument("--max-workers", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument(
        "--keep-images",
        action="store_true",
        help="keep the ~4GB-per-instance eval images after grading",
    )
    args = parser.parse_args()

    run_dir = RESULTS_DIR / args.run_id
    if not run_dir.is_dir():
        print(f"Unknown run: {run_dir}")
        return 2

    ready, message = is_docker_ready()
    print(message)
    if not ready:
        return 3

    report = evaluate(
        run_dir,
        max_workers=args.max_workers,
        timeout=args.timeout,
        keep_images=args.keep_images,
    )
    # The harness only submits instances with a non-empty patch; count the whole
    # slice as the denominator so empty patches are not silently excluded.
    expected = len(json.loads(_predictions(run_dir).read_text(encoding="utf-8")))
    resolved = report.get("resolved_instances", 0)
    rate = (resolved / expected) if expected else 0.0
    print(f"\nOfficial harness: {resolved}/{expected} resolved ({rate:.1%})"
          f" — {report.get('total_instances', 0)} submitted")
    print(f"Report: {run_dir / 'harness_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
