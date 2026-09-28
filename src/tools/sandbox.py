"""
ISHA Sandbox — Local test execution for candidate patches.

Copies the target repo into an isolated scratch directory, applies the
candidate patch there (never mutating the real repo), runs pytest and
captures stdout+stderr for the self-correction loop.

pytest runs on the host by default; set ``ISHA_SANDBOX_MODE=docker`` to
execute it inside a throwaway container instead (see `docker_sandbox.py`).
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from src.ingestion.parser import SKIP_DIRS
from src.tools import docker_sandbox
from src.tools.patch_engine import apply_patch

DEFAULT_TIMEOUT = 180


def copy_repo(src: str, dest: str) -> str:
    """Copy a repository into `dest`, skipping caches, venvs and git metadata."""
    if os.path.isdir(dest):
        shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(
        src,
        dest,
        ignore=shutil.ignore_patterns(*SKIP_DIRS, "*.pyc"),
    )
    return dest


def make_sandbox(repo_path: str, prefix: str = "isha-sandbox-") -> str:
    """Create a fresh, isolated copy of a repository."""
    dest = Path(tempfile.mkdtemp(prefix=prefix))
    return copy_repo(str(Path(repo_path).resolve()), str(dest))


def cleanup_sandbox(sandbox_path: str) -> None:
    """Delete a scratch sandbox directory."""
    if sandbox_path and os.path.isdir(sandbox_path):
        shutil.rmtree(sandbox_path, ignore_errors=True)


def run_tests(repo_path: str, timeout: int = DEFAULT_TIMEOUT, test_file: str | None = None) -> str:
    """Execute pytest for a sandbox and return combined output.

    Runs inside a throwaway Docker container when ``ISHA_SANDBOX_MODE=docker``
    (see `src/tools/docker_sandbox.py`), falling back to the local subprocess
    runner whenever Docker is unavailable or fails for infrastructure reasons.

    When `test_file` is given only that file runs (the generated regression
    test), otherwise the whole sandbox is exercised.
    """
    if docker_sandbox.enabled():
        output = docker_sandbox.run_tests_docker(
            repo_path, timeout=timeout, test_file=test_file
        )
        if output is not None:
            return output
    return _run_tests_local(repo_path, timeout=timeout, test_file=test_file)


def _run_tests_local(
    repo_path: str, timeout: int = DEFAULT_TIMEOUT, test_file: str | None = None
) -> str:
    if not repo_path or not os.path.isdir(repo_path):
        return "FAILED: sandbox directory missing"

    target = "."
    if test_file:
        candidate = os.path.join(repo_path, test_file)
        if not os.path.exists(candidate):
            return f"FAILED: missing test file {test_file}"
        target = test_file

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
