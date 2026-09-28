"""
ISHA Patch Validity Gates — cheap static checks applied before any test run.

A patch that does not parse is never worth spending a test run on, so every
candidate goes through:

  1. apply        the diff must apply to a clean checkout
  2. compile      ``ast.parse`` / ``py_compile`` on every changed Python file
  3. pyflakes     no undefined names / unused-but-broken imports

Failures are returned as structured results so the caller can feed the exact
error back to the coder for a retry instead of guessing.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

_DIFF_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$", re.M)
_PY_EXT = ".py"


@dataclass
class GateResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    added_lines: int = 0
    removed_lines: int = 0

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "changed_files": self.changed_files,
            "added_lines": self.added_lines,
            "removed_lines": self.removed_lines,
        }


def changed_files(patch: str) -> list[str]:
    """Paths touched by a unified diff (``b/`` side preferred)."""
    files = []
    for match in _DIFF_FILE_RE.finditer(patch or ""):
        path = match.group(1).strip()
        if path != "/dev/null" and path not in files:
            files.append(path)
    if not files:
        for match in re.finditer(r"^--- a/(.+)$", (patch or ""), re.M):
            if match.group(1).strip() not in files:
                files.append(match.group(1).strip())
    return files


def diff_stats(patch: str) -> tuple[int, int]:
    added = removed = 0
    for line in (patch or "").splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
    return added, removed


def _check_python(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: unreadable ({exc})"]
    try:
        ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        errors.append(f"{path}: SyntaxError line {exc.lineno}: {exc.msg}")
        return errors

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pyflakes", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except Exception:
        return errors  # pyflakes unavailable — ast.parse already passed
    if proc.returncode not in (0, 1):
        return errors
    for line in (proc.stdout or "").splitlines():
        # pyflakes prints "<file>:<line>:<col>: message"
        msg = line.split(": ", 1)[-1] if ": " in line else line
        if "unable to detect undefined names" in msg:
            continue
        errors.append(f"{path}: {msg}")
    return errors


def _message_only(text: str) -> str:
    """Drop the (sandbox-specific) file prefix so errors can be compared."""
    return text.split(": ", 1)[-1] if ": " in text else text


def _baseline_errors(baseline_repo: str | None, rel: str) -> set[str]:
    """Errors the *pristine* file already has.

    Large codebases ship with pre-existing pyflakes findings (`undefined
    name '_ASTROPY_SETUP_'` in generated C-extension shims, unused locals,
    ...).  Gating on them would reject correct patches for code the model
    never touched, so only findings the patch *introduces* are fatal.
    """
    if not baseline_repo:
        return set()
    source = Path(baseline_repo) / rel
    if not source.is_file():
        return set()
    return {_message_only(e) for e in _check_python(source)}


def compile_gate(repo_path: str, patch: str, baseline_repo: str | None = None) -> GateResult:
    """Run the static gates over a candidate patch in ``repo_path``.

    ``baseline_repo`` is the untouched checkout the patch was written
    against; passing it lets the gate subtract pre-existing findings.
    """
    files = changed_files(patch)
    added, removed = diff_stats(patch)
    result = GateResult(ok=True, changed_files=files, added_lines=added, removed_lines=removed)

    if not (patch or "").strip():
        result.ok = False
        result.errors.append("empty patch")
        return result

    root = Path(repo_path)
    for rel in files:
        target = root / rel
        if not target.is_file():
            # A deleted file or a path written with a stray prefix is fine to
            # skip here — the apply gate already proved the diff lands.
            continue
        if target.suffix != _PY_EXT:
            continue
        known = _baseline_errors(baseline_repo, rel)
        for error in _check_python(target):
            if "SyntaxError" in error:
                result.errors.append(error)   # never pre-existing-safe
                continue
            if _message_only(error) in known:
                continue
            result.errors.append(error)
    result.ok = not result.errors
    return result


def apply_gate(repo_path: str, patch: str, baseline_repo: str | None = None) -> tuple[bool, str]:
    """Apply the patch to a scratch copy; returns (ok, exact_error_message)."""
    from src.tools.patch_engine import apply_patch
    from src.tools.sandbox import cleanup_sandbox, make_sandbox

    sandbox = make_sandbox(repo_path)
    try:
        ok, message = apply_patch(sandbox, patch)
        if not ok:
            return False, message
        gate = compile_gate(sandbox, patch, baseline_repo=baseline_repo)
        if not gate.ok:
            return False, "STATIC GATE: " + "; ".join(gate.errors)
        return True, message
    finally:
        cleanup_sandbox(sandbox)
