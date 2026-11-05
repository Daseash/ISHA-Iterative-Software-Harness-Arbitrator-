"""
ISHA SWE-bench checkouts — resumable, mirror-backed preparation.

Each instance needs its repository checked out at ``base_commit`` so the
solver can read and patch it.  Cloning 30+ copies of django/sympy from GitHub
is slow, so every repo is mirrored once into ``swebench_checkouts/.mirrors``
and each instance is a local ``--shared`` clone of that mirror (instant, no
network).  Instances that already sit on the right commit are skipped.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKOUTS = ROOT / "swebench_checkouts"
MIRRORS = CHECKOUTS / ".mirrors"

GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_TERMINAL_PROGRESS": "0"}


class CheckoutError(RuntimeError):
    pass


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 1800) -> str:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=GIT_ENV,
        )
    except subprocess.TimeoutExpired as exc:
        raise CheckoutError(f"{' '.join(cmd)} timed out after {timeout}s") from exc
    if proc.returncode != 0:
        raise CheckoutError(
            f"{' '.join(cmd)} -> {(proc.stderr or proc.stdout).strip()[:400]}"
        )
    return (proc.stdout or "").strip()


def checkout_path(instance_id: str) -> Path:
    return CHECKOUTS / instance_id.replace("/", "__")


def mirror_path(repo: str) -> Path:
    return MIRRORS / (repo.replace("/", "__") + ".git")


def ensure_mirror(repo: str, timeout: int = 3600) -> Path:
    """Clone (once) or refresh the bare mirror for ``repo``."""
    dest = mirror_path(repo)
    url = f"https://github.com/{repo}.git"
    if dest.is_dir() and (dest / "HEAD").is_file():
        try:
            _run(["git", "--git-dir", str(dest), "remote", "update", "--prune"], timeout=timeout)
            return dest
        except CheckoutError:
            # Refresh failed (offline?) — a stale mirror is still usable.
            return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        import shutil

        shutil.rmtree(dest, ignore_errors=True)
    _run(["git", "clone", "--bare", url, str(dest)], timeout=timeout)
    return dest


def prepare(record: dict, refresh: bool = False) -> str:
    """Make sure the instance checkout exists at its base commit.

    Returns a status label: ``up-to-date`` | ``cloned``.
    """
    dest = checkout_path(record["instance_id"])
    commit = record["base_commit"]

    if dest.is_dir() and (dest / ".git").exists() and not refresh:
        try:
            if _run(["git", "rev-parse", "HEAD"], cwd=dest) == commit:
                _run(["git", "config", "core.autocrlf", "false"], cwd=dest, timeout=60)
                return "up-to-date"
        except CheckoutError:
            pass

    mirror = ensure_mirror(record["repo"])
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and not (dest / ".git").exists():
        import shutil

        shutil.rmtree(dest, ignore_errors=True)

    if not (dest / ".git").exists():
        # Local clone of the mirror: no network, shares object storage.
        _run(["git", "clone", "--shared", str(mirror), str(dest)], timeout=1800)
        _run(["git", "config", "core.autocrlf", "false"], cwd=dest, timeout=60)

    _checkout_at(dest, commit, record)
    return "cloned"


def _checkout_at(dest: Path, commit: str, record: dict) -> None:
    """Check out ``commit``, retrying Windows' transient unlink failures.

    ``unable to unlink old ... Invalid argument`` shows up when an indexer or
    AV holds a file for a moment; one retry clears it, and a full re-clone
    from the local mirror is the last resort so a single locked file cannot
    cost us an instance.
    """
    import shutil
    import time

    last: Exception | None = None
    for attempt in range(3):
        try:
            _run(["git", "checkout", "-q", "--force", commit], cwd=dest, timeout=600)
            _run(["git", "clean", "-xfdq"], cwd=dest, timeout=600)
            if _run(["git", "rev-parse", "HEAD"], cwd=dest) == commit:
                return
            last = CheckoutError("HEAD does not match the requested commit")
        except Exception as exc:  # noqa: BLE001 - recorded and retried
            last = exc
        time.sleep(3 * (attempt + 1))

    # Nothing else worked: drop the tree and re-clone it from the mirror.
    shutil.rmtree(dest, ignore_errors=True)
    mirror = ensure_mirror(record["repo"])
    _run(["git", "clone", "--shared", str(mirror), str(dest)], timeout=1800)
    _run(["git", "config", "core.autocrlf", "false"], cwd=dest, timeout=60)
    _run(["git", "checkout", "-q", "--force", commit], cwd=dest, timeout=600)
    _run(["git", "clean", "-xfdq"], cwd=dest, timeout=600)
    if _run(["git", "rev-parse", "HEAD"], cwd=dest) != commit:
        raise last or CheckoutError(f"could not check out {commit}")


def ensure_all(records: list[dict], refresh: bool = False) -> tuple[int, list[str]]:
    """Prepare every instance; returns (ok_count, failures)."""
    ok, failures = 0, []
    for i, record in enumerate(records, start=1):
        iid = record["instance_id"]
        try:
            status = prepare(record, refresh=refresh)
            print(f"  [{i}/{len(records)}] {iid:<40} {status}", flush=True)
            ok += 1
        except Exception as exc:
            failures.append(f"{iid}: {exc}")
            print(f"  [{i}/{len(records)}] {iid:<40} FAILED: {exc}", flush=True)
    return ok, failures
