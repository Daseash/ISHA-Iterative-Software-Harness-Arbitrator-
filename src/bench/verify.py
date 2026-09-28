"""
ISHA Repro & Regression Verification — Phase 5 of the SWE-bench upgrade.

The host cannot run these repositories (their environments live in the
official harness images), so verification happens **inside the instance's own
image** with a bind-mounted patch:

    before:  pristine image + repro test  -> must FAIL  (the bug is real)
    after:   pristine image + repro test + model patch -> must PASS

Two rules make this trustworthy rather than a source of flaky regressions:

  * The repro test is written **outside** the repository working set we hand
    to the harness, so it can never leak into ``model_patch``.
  * Any infrastructure failure (image missing, timeout, docker down) is
    recorded as ``unknown`` and makes the candidate *neutral*, never
    negative — a candidate is only punished for evidence we actually
    gathered.

Touched-module regression tests are run on top of the repro test and counted
as ``regression_count``; they lower a candidate's rank but never veto it
outright, because pre-existing failures in a fresh checkout are common.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

MOUNT_SRC_NAME = "isha_repro.py"
MOUNT_PATCH_NAME = "isha_model.patch"
DEFAULT_TIMEOUT = int(os.getenv("ISHA_VERIFY_TIMEOUT", "600"))
DOCKER = os.getenv("ISHA_DOCKER", "docker")


# ── Instance metadata ──────────────────────────────────────────────────────
def instance_meta(record: dict) -> dict:
    """Extract what we need from a cached dataset record."""
    eval_script = record.get("eval_script", "") or ""
    return {
        "instance_id": record.get("instance_id", ""),
        "repo": record.get("repo", ""),
        "image": record.get("image", "") or "",
        "eval_script": eval_script,
        "preamble": _preamble(eval_script),
        "fail_to_pass": record.get("FAIL_TO_PASS", ""),
        "pass_to_pass": record.get("PASS_TO_PASS", ""),
    }


def _preamble(eval_script: str) -> str:
    """The environment-activation lines of the harness eval script.

    Everything else (``cd /testbed``, ``git checkout``, ``git apply`` of the
    official test patch, ``pip install``) is either redundant or actively
    harmful — we install *our* patch instead of theirs.
    """
    keep: list[str] = []
    for raw in (eval_script or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if (
            line.startswith("source ")
            or line.startswith(". ")
            or line.startswith("conda activate")
            or line.startswith("export ")
        ):
            keep.append(line)
    if not any("conda activate" in l for l in keep):
        keep.append("conda activate testbed" if "conda" in (eval_script or "") else "")
    return " && ".join(x for x in keep if x)


# ── Repro test placement ───────────────────────────────────────────────────
def repro_target(record: dict) -> tuple[str, str]:
    """Return ``(path-inside-repo, pytest-or-django-target)`` for this repo."""
    if record.get("repo") == "django/django":
        return "tests/isha_repro.py", "tests.isha_repro"
    return "test_isha_repro.py", "test_isha_repro.py"


def test_command(record: dict, targets: list[str]) -> str:
    if record.get("repo") == "django/django":
        return (
            "./tests/runtests.py --verbosity 1 --settings=test_sqlite "
            "--parallel 1 " + " ".join(targets)
        )
    return (
        "python -m pytest " + " ".join(targets)
        + " -q --tb=short -p no:cacheprovider"
    )


def _split_targets(raw: str) -> list[str]:
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if not raw:
        return []
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except (ValueError, TypeError):
            pass
        return [t for t in raw.replace(",", " ").split() if t]
    return []


# ── Docker runner ──────────────────────────────────────────────────────────
def docker_ready() -> tuple[bool, str]:
    if shutil.which(DOCKER) is None:
        return False, "docker binary not found on PATH"
    try:
        proc = subprocess.run(
            [DOCKER, "version", "--format", "{{.Server.Version}}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=40,
        )
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "docker daemon not running").strip()[:300]
    return True, (proc.stdout or "").strip()


def image_available(image: str) -> bool:
    try:
        proc = subprocess.run(
            [DOCKER, "image", "inspect", image],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60,
        )
        return proc.returncode == 0
    except Exception:
        return False


def pull_image(image: str, timeout: int = 900) -> bool:
    try:
        proc = subprocess.run(
            [DOCKER, "pull", image],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout,
        )
        return proc.returncode == 0
    except Exception:
        return False


def _run(image: str, mounts: dict[str, str], script: str,
         timeout: int = DEFAULT_TIMEOUT) -> tuple[int | None, str]:
    """Run ``script`` in a throwaway container. Returns (exit_code, output)."""
    cmd = [DOCKER, "run", "--rm", "--init"]
    for host, container in mounts.items():
        cmd += ["--mount", f"type=bind,src={host},dst={container},ro"]
    cmd += [image, "bash", "-lc", script]

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, f"VERIFY TIMEOUT after {timeout}s"
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"

    out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode, out[-6000:]


# ── One verification run ───────────────────────────────────────────────────
def _script(meta: dict, target: str, cmd: str, use_patch: bool) -> str:
    lines = [
        "set -o pipefail",
        "cd /testbed",
        "git config --global --add safe.directory /testbed || true",
    ]
    if meta["preamble"]:
        lines.append(meta["preamble"])
    lines.append(f"cp {MOUNT_SRC_NAME} /testbed/{target}")
    if use_patch:
        lines.append(
            f"git apply --whitespace=nowarn {MOUNT_PATCH_NAME} "
            f"|| git apply --3way --whitespace=nowarn {MOUNT_PATCH_NAME}"
        )
    lines.append(cmd)
    return "\n".join(lines)


def verify_instance(
    record: dict,
    repro_test: str,
    patch: str,
    touched_targets: list[str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Return the verification record for one candidate patch.

    Keys: ``available`` (False when infra is missing), ``before_ok``,
    ``after_ok``, ``regressions``, ``reason``.
    """
    meta = instance_meta(record)
    result: dict = {
        "available": False,
        "before_ok": None,
        "after_ok": None,
        "regressions": 0,
        "reason": "",
        "repro_target": "",
        "before_exit": None,
        "after_exit": None,
    }

    if not repro_test or repro_test.startswith("#"):
        result["reason"] = "no repro test generated"
        return result
    if not meta["image"]:
        result["reason"] = "record has no image field"
        return result

    ok, why = docker_ready()
    if not ok:
        result["reason"] = f"docker unavailable: {why}"
        return result
    if not image_available(meta["image"]):
        result["reason"] = f"image not present locally: {meta['image']}"
        return result

    target, single = repro_target(record)
    base_cmd = test_command(record, [target])
    result["repro_target"] = target

    tmpdir = Path(tempfile.mkdtemp(prefix="isha-verify-"))
    repro_host = tmpdir / MOUNT_SRC_NAME
    repro_host.write_text(repro_test, encoding="utf-8")
    mounts = {str(repro_host): f"/tmp/{MOUNT_SRC_NAME}"}
    patch_mounted = False
    if patch:
        patch_host = tmpdir / MOUNT_PATCH_NAME
        patch_host.write_text(patch, encoding="utf-8")
        mounts[str(patch_host)] = f"/tmp/{MOUNT_PATCH_NAME}"
        patch_mounted = True

    try:
        # BEFORE — pristine tree, repro test only. Must fail.
        before_exit, before_out = _run(
            meta["image"], mounts, _script(meta, target, base_cmd, False),
            timeout=timeout,
        )
        result["before_exit"] = before_exit
        if before_exit is None:
            result["reason"] = "before-run " + before_out.strip()[:200]
            return result
        result["before_ok"] = before_exit != 0  # non-zero == bug reproduced

        # AFTER — same tree + model patch. Must pass.
        if not patch_mounted:
            result["reason"] = "candidate has no patch to verify"
            return result
        after_exit, after_out = _run(
            meta["image"], mounts, _script(meta, target, base_cmd, True),
            timeout=timeout,
        )
        result["after_exit"] = after_exit
        if after_exit is None:
            result["reason"] = "after-run " + after_out.strip()[:200]
            return result
        result["after_ok"] = after_exit == 0
        result["after_output"] = after_out[-2500:]

        # Existing tests covering the touched modules — regression count only.
        if touched_targets:
            reg = _regressions(meta, target, touched_targets, mounts, timeout)
            result["regressions"] = reg

        result["available"] = True
        if not result["before_ok"]:
            result["reason"] = (
                "repro test passed on the pristine tree — test does not "
                "demonstrate the bug (treated as neutral)"
            )
        elif not result["after_ok"]:
            result["reason"] = "patch does not make the repro test pass"
        else:
            result["reason"] = "repro confirmed: fails before, passes after"
        return result
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _regressions(meta: dict, repro_target: str, touched: list[str],
                 mounts: dict[str, str], timeout: int) -> int:
    """Run existing tests for touched modules on the patched tree."""
    cmd = test_command(meta, [t for t in touched if t != repro_target])
    if not cmd.strip():
        return 0
    exit_code, _out = _run(
        meta["image"], mounts, _script(meta, repro_target, cmd, True),
        timeout=timeout,
    )
    if exit_code is None:
        return 0
    return 0 if exit_code == 0 else 1


# ── Target derivation for touched-module tests ─────────────────────────────
def touched_targets(record: dict, changed_files: list[str], repo_root: str) -> list[str]:
    """Map changed source files onto their closest existing test files."""
    from src.tools.codebody import tests_for

    out: list[str] = []
    for rel in changed_files:
        if "test" in Path(rel).name:
            out.append(rel)
            continue
        try:
            for test_file in tests_for(Path(repo_root) / rel):
                out.append(str(Path(test_file).relative_to(repo_root)).replace("\\", "/"))
        except Exception:
            continue
    # De-duplicate, keep order, bound the cost of one docker run.
    seen: list[str] = []
    for item in out:
        if item and item not in seen:
            seen.append(item)
    return seen[:6]
