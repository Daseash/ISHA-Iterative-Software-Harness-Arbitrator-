"""
ISHA Docker sandbox — execute pytest inside an isolated container.

When ``ISHA_SANDBOX_MODE=docker`` the sandbox directory (a host-side scratch
copy the coder has already edited) is bind-mounted into a throwaway container
so the suite runs against the container's interpreter and site-packages
instead of the host's. The container is removed after every run.

Everything degrades gracefully: if the Docker CLI or daemon is unavailable,
or the run fails for infrastructure reasons, :func:`run_tests_docker` returns
``None`` and the caller falls back to the local subprocess runner, so the
agent never hard-fails because Docker is missing.
"""

import os
import shutil
import subprocess
import uuid
from pathlib import Path

DEFAULT_IMAGE = "isha-sandbox:latest"
DEFAULT_TIMEOUT = 180

# docker CLI / daemon failure exit codes — never pytest results
_INFRA_EXIT_CODES = (125, 126, 127)

_docker_checked: bool | None = None


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def docker_available() -> bool:
    """True when the Docker CLI exists and can reach a daemon (cached)."""
    global _docker_checked
    if _docker_checked is None:
        if not shutil.which("docker"):
            _docker_checked = False
        else:
            try:
                proc = subprocess.run(
                    ["docker", "version"], capture_output=True, timeout=15
                )
                _docker_checked = proc.returncode == 0
            except Exception:
                _docker_checked = False
    return _docker_checked


def enabled() -> bool:
    """True when containerised test execution is requested and possible."""
    if _env("ISHA_SANDBOX_MODE", "local").strip().lower() != "docker":
        return False
    return docker_available()


def build_command(
    repo_path: str,
    test_file: str | None = None,
    image: str | None = None,
    name: str | None = None,
) -> list:
    """Build the ``docker run`` argv that executes pytest on `repo_path`."""
    image = image or _env("ISHA_SANDBOX_IMAGE", DEFAULT_IMAGE)
    name = name or f"isha-sbx-{uuid.uuid4().hex[:12]}"
    mount = str(Path(repo_path).resolve())
    target = test_file or "."

    cmd = [
        "docker",
        "run",
        "--rm",
        "--name",
        name,
        "-v",
        f"{mount}:/workspace:rw",
        "-w",
        "/workspace",
        "-e",
        "PYTHONIOENCODING=utf-8",
    ]
    network = _env("ISHA_SANDBOX_NETWORK", "none")
    if network:
        cmd += ["--network", network]
    memory = _env("ISHA_SANDBOX_MEMORY", "1g")
    if memory:
        cmd += ["--memory", memory]
    cpus = _env("ISHA_SANDBOX_CPUS", "2")
    if cpus:
        cmd += ["--cpus", cpus]
    user = _env("ISHA_SANDBOX_USER", "")
    if user:
        cmd += ["--user", user]

    cmd += [
        image,
        "python",
        "-m",
        "pytest",
        target,
        "-q",
        "--tb=short",
        "-p",
        "no:cacheprovider",
    ]
    return cmd


def _remove_container(name: str) -> None:
    """Best-effort force-removal of a named container."""
    try:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=15)
    except Exception:
        pass


def run_tests_docker(
    repo_path: str, timeout: int = DEFAULT_TIMEOUT, test_file: str | None = None
) -> str | None:
    """Run pytest for `repo_path` inside a throwaway container.

    Returns the raw combined pytest output (byte-for-byte what the local
    runner would produce, so verdict parsing is unaffected), a ``FAILED:``
    marker for sandbox problems, or ``None`` when Docker itself could not run
    the suite and the caller should fall back to the local runner.
    """
    if not repo_path or not os.path.isdir(repo_path):
        return "FAILED: sandbox directory missing"
    if test_file and not os.path.exists(os.path.join(repo_path, test_file)):
        return f"FAILED: missing test file {test_file}"

    cmd = build_command(repo_path, test_file=test_file)
    name = cmd[cmd.index("--name") + 1]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        _remove_container(name)
        return f"FAILED: tests timed out after {timeout}s"
    except (FileNotFoundError, OSError):
        return None

    combined = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode in _INFRA_EXIT_CODES:
        return None
    if not combined.strip():
        if proc.returncode == 0:
            return None
        return f"FAILED: sandbox container exited with code {proc.returncode}"
    return combined.strip()
