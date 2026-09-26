"""
ISHA Sandbox — Local test execution for candidate patches.

Copies the target repo into an isolated scratch directory, applies the
candidate patch there (never mutating the real repo), runs pytest and
captures stdout+stderr for the self-correction loop.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from src.ingestion.parser import SKIP_DIRS
from src.tools.patch_engine import apply_patch

DEFAULT_TIMEOUT = 180


def make_sandbox(repo_path: str, prefix: str = "isha-sandbox-") -> str:
    """Create a fresh, isolated copy of a repository."""
    src = Path(repo_path).resolve()
    dest = Path(tempfile.mkdtemp(prefix=prefix))
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(
        src,
        dest,
        ignore=shutil.ignore_patterns(*SKIP_DIRS, "*.pyc", ".git"),
    )
    return str(dest)


def cleanup_sandbox(sandbox_path: str) -> None:
    """Delete a scratch sandbox directory."""
    if sandbox_path and os.path.isdir(sandbox_path):
        shutil.rmtree(sandbox_path, ignore_errors=True)


def run_tests(repo_path: str, timeout: int = DEFAULT_TIMEOUT, test_file: str | None = None) -> str:
    """Execute pytest in a sandboxed directory and return combined output.

    When `test_file` is given only that file runs (the generated regression
    test), otherwise the whole sandbox is exercised.
    """
    if not repo_path or not os.path.isdir(repo_path):
        return "FAILED: sandbox directory missing"

    target = repo_path
    if test_file:
        candidate = os.path.join(repo_path, test_file)
        if not os.path.exists(candidate):
            return f"FAILED: missing test file {test_file}"
        target = candidate

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", target, "-q", "--tb=short", "-p", "no:cacheprovider"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
        return (proc.stdout + proc.stderr).strip()
    except subprocess.TimeoutExpired:
        return f"FAILED: tests timed out after {timeout}s"
    except Exception as exc:
        return f"FAILED: sandbox error: {exc}"


def run_in_sandbox(
    repo_path: str, diff_text: str, timeout: int = DEFAULT_TIMEOUT, test_file: str | None = None
) -> tuple:
    """Apply a patch in a fresh sandbox and run the test suite.

    Returns (sandbox_path, test_output). Caller owns the sandbox directory.
    """
    sandbox = make_sandbox(repo_path)
    ok, message = apply_patch(sandbox, diff_text)
    if not ok:
        return sandbox, f"FAILED: patch could not be applied — {message}"
    return sandbox, run_tests(sandbox, timeout=timeout, test_file=test_file)
