import subprocess

import pytest

import src.tools.docker_sandbox as docker_sandbox
from src.tools import sandbox as sandbox_mod


@pytest.fixture(autouse=True)
def _docker_state(monkeypatch):
    for var in (
        "ISHA_SANDBOX_MODE",
        "ISHA_SANDBOX_IMAGE",
        "ISHA_SANDBOX_NETWORK",
        "ISHA_SANDBOX_MEMORY",
        "ISHA_SANDBOX_CPUS",
        "ISHA_SANDBOX_USER",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(docker_sandbox, "_docker_checked", False)


def _fail(*args, **kwargs):
    pytest.fail("docker must not be invoked")


# ── command construction ───────────────────────────────────────────────────


def test_build_command_mounts_workspace_and_targets_test_file(tmp_path, monkeypatch):
    monkeypatch.setenv("ISHA_SANDBOX_MODE", "docker")
    cmd = docker_sandbox.build_command(
        str(tmp_path), test_file="test_regression_isha.py"
    )

    assert cmd[:3] == ["docker", "run", "--rm"]
    mount_arg = cmd[cmd.index("-v") + 1]
    assert mount_arg == f"{tmp_path.resolve()}:/workspace:rw"
    assert cmd[cmd.index("-w") + 1] == "/workspace"
    assert cmd[cmd.index("-e") + 1] == "PYTHONIOENCODING=utf-8"

    pytest_target = cmd[cmd.index("pytest") + 1]
    assert pytest_target == "test_regression_isha.py"
    assert cmd[-1] == "no:cacheprovider"


def test_build_command_defaults_to_workspace_root(tmp_path):
    cmd = docker_sandbox.build_command(str(tmp_path))
    assert cmd[cmd.index("pytest") + 1] == "."


def test_build_command_includes_resource_limits(tmp_path, monkeypatch):
    monkeypatch.setenv("ISHA_SANDBOX_NETWORK", "none")
    monkeypatch.setenv("ISHA_SANDBOX_MEMORY", "1g")
    monkeypatch.setenv("ISHA_SANDBOX_CPUS", "2")
    monkeypatch.setenv("ISHA_SANDBOX_IMAGE", "custom:tag")

    cmd = docker_sandbox.build_command(str(tmp_path))

    assert cmd[cmd.index("--network") + 1] == "none"
    assert cmd[cmd.index("--memory") + 1] == "1g"
    assert cmd[cmd.index("--cpus") + 1] == "2"
    assert "custom:tag" in cmd
    assert "--user" not in cmd


def test_build_command_omits_empty_limits(tmp_path, monkeypatch):
    monkeypatch.setenv("ISHA_SANDBOX_NETWORK", "")
    monkeypatch.setenv("ISHA_SANDBOX_MEMORY", "")
    monkeypatch.setenv("ISHA_SANDBOX_CPUS", "")

    cmd = docker_sandbox.build_command(str(tmp_path))

    assert "--network" not in cmd
    assert "--memory" not in cmd
    assert "--cpus" not in cmd


def test_build_command_every_run_gets_a_unique_container_name(tmp_path):
    def name_of(cmd):
        return cmd[cmd.index("--name") + 1]

    first = docker_sandbox.build_command(str(tmp_path))
    second = docker_sandbox.build_command(str(tmp_path))
    assert name_of(first) != name_of(second)


# ── enabled() gating ───────────────────────────────────────────────────────


def test_enabled_requires_docker_mode(monkeypatch):
    monkeypatch.setattr(docker_sandbox, "docker_available", lambda: True)

    monkeypatch.setenv("ISHA_SANDBOX_MODE", "docker")
    assert docker_sandbox.enabled() is True

    monkeypatch.setenv("ISHA_SANDBOX_MODE", "local")
    assert docker_sandbox.enabled() is False

    monkeypatch.delenv("ISHA_SANDBOX_MODE")
    assert docker_sandbox.enabled() is False


def test_enabled_false_when_docker_missing(monkeypatch):
    monkeypatch.setenv("ISHA_SANDBOX_MODE", "docker")
    monkeypatch.setattr(docker_sandbox, "docker_available", lambda: False)
    assert docker_sandbox.enabled() is False


# ── run_tests dispatch ─────────────────────────────────────────────────────


def test_local_mode_never_touches_docker(tmp_path, monkeypatch):
    monkeypatch.setattr(docker_sandbox, "docker_available", lambda: True)
    monkeypatch.setattr(docker_sandbox, "run_tests_docker", _fail)
    monkeypatch.setattr(sandbox_mod, "_run_tests_local", lambda *a, **k: "LOCAL")

    assert sandbox_mod.run_tests(str(tmp_path)) == "LOCAL"


def test_docker_mode_falls_back_when_cli_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("ISHA_SANDBOX_MODE", "docker")
    monkeypatch.setattr(docker_sandbox, "docker_available", lambda: False)
    monkeypatch.setattr(docker_sandbox, "run_tests_docker", _fail)
    monkeypatch.setattr(sandbox_mod, "_run_tests_local", lambda *a, **k: "LOCAL")

    assert sandbox_mod.run_tests(str(tmp_path)) == "LOCAL"


def test_docker_mode_falls_back_on_infrastructure_error(tmp_path, monkeypatch):
    monkeypatch.setenv("ISHA_SANDBOX_MODE", "docker")
    monkeypatch.setattr(docker_sandbox, "docker_available", lambda: True)
    monkeypatch.setattr(
        docker_sandbox, "run_tests_docker", lambda *a, **k: None
    )
    monkeypatch.setattr(sandbox_mod, "_run_tests_local", lambda *a, **k: "LOCAL")

    assert sandbox_mod.run_tests(str(tmp_path)) == "LOCAL"


def test_docker_mode_returns_container_output(tmp_path, monkeypatch):
    monkeypatch.setenv("ISHA_SANDBOX_MODE", "docker")
    monkeypatch.setattr(docker_sandbox, "docker_available", lambda: True)
    monkeypatch.setattr(
        docker_sandbox, "run_tests_docker", lambda *a, **k: "2 passed, 1 failed"
    )
    monkeypatch.setattr(sandbox_mod, "_run_tests_local", _fail)

    assert sandbox_mod.run_tests(str(tmp_path)) == "2 passed, 1 failed"


# ── run_tests_docker ───────────────────────────────────────────────────────


def test_missing_sandbox_directory(tmp_path):
    out = docker_sandbox.run_tests_docker(str(tmp_path / "nope"))
    assert out == "FAILED: sandbox directory missing"


def test_missing_test_file_short_circuits(tmp_path, monkeypatch):
    monkeypatch.setattr(docker_sandbox.subprocess, "run", _fail)
    out = docker_sandbox.run_tests_docker(str(tmp_path), test_file="absent.py")
    assert out == "FAILED: missing test file absent.py"


def test_pytest_output_returned_verbatim(tmp_path, monkeypatch):
    def fake_run(cmd, **kwargs):
        if cmd[1] == "rm":
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return subprocess.CompletedProcess(cmd, 1, "2 passed, 1 failed in 0.05s\n", "")

    monkeypatch.setattr(docker_sandbox.subprocess, "run", fake_run)
    out = docker_sandbox.run_tests_docker(str(tmp_path))
    assert out == "2 passed, 1 failed in 0.05s"


def test_docker_cli_failure_returns_none(tmp_path, monkeypatch):
    def fake_run(cmd, **kwargs):
        if cmd[1] == "rm":
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return subprocess.CompletedProcess(
            cmd, 125, "", "docker: Cannot connect to the Docker daemon.\n"
        )

    monkeypatch.setattr(docker_sandbox.subprocess, "run", fake_run)
    assert docker_sandbox.run_tests_docker(str(tmp_path)) is None


def test_timeout_removes_container_and_reports_failure(tmp_path, monkeypatch):
    removed = []

    def fake_run(cmd, **kwargs):
        if cmd[1] == "rm":
            removed.append(cmd[cmd.index("-f") + 1])
            return subprocess.CompletedProcess(cmd, 0, "", "")
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 0))

    monkeypatch.setattr(docker_sandbox.subprocess, "run", fake_run)
    out = docker_sandbox.run_tests_docker(str(tmp_path), timeout=5)
    assert out == "FAILED: tests timed out after 5s"
    assert removed and removed[0].startswith("isha-sbx-")


def test_empty_crash_output_reports_failure(tmp_path, monkeypatch):
    def fake_run(cmd, **kwargs):
        if cmd[1] == "rm":
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return subprocess.CompletedProcess(cmd, 137, "", "")

    monkeypatch.setattr(docker_sandbox.subprocess, "run", fake_run)
    out = docker_sandbox.run_tests_docker(str(tmp_path))
    assert out == "FAILED: sandbox container exited with code 137"


# ── end-to-end (local runner still works after the refactor) ───────────────


def test_local_runner_executes_pytest(tmp_path):
    (tmp_path / "test_ok.py").write_text(
        "def test_ok():\n    assert True\n", encoding="utf-8"
    )
    out = sandbox_mod._run_tests_local(str(tmp_path))
    assert "1 passed" in out
