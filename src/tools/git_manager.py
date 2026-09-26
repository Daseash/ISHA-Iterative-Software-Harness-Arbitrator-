"""
ISHA Git Manager — Branch creation, rollback, and commit management.

Thin subprocess wrappers used by the sandbox and merger nodes.
"""

import subprocess
from pathlib import Path


def _git(repo_path: str, *args: str, timeout: int = 60) -> tuple:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return proc.returncode == 0, (proc.stdout + proc.stderr).strip()
    except Exception as exc:
        return False, str(exc)


def create_branch(repo_path: str, branch_name: str) -> bool:
    """Create a new git branch for the fix attempt."""
    if not repo_path or not (Path(repo_path) / ".git").exists():
        return False
    ok, _ = _git(repo_path, "checkout", "-b", branch_name)
    if ok:
        return True
    return _git(repo_path, "checkout", branch_name)[0]


def commit_fix(repo_path: str, message: str) -> bool:
    """Commit the applied patch with a descriptive message."""
    if not repo_path or not (Path(repo_path) / ".git").exists():
        return False
    _git(repo_path, "add", "-A")
    ok, _ = _git(repo_path, "commit", "-m", message)
    if ok:
        return True
    # Nothing staged / nothing to commit is treated as failure.
    return False


def rollback(repo_path: str) -> bool:
    """Rollback to the previous clean state."""
    if not repo_path or not (Path(repo_path) / ".git").exists():
        return False
    ok, _ = _git(repo_path, "checkout", "--", ".")
    _git(repo_path, "clean", "-fd")
    return ok
