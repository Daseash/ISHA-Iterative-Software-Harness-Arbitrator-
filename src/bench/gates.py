"""
ISHA Patch Validity Gates — cheap static checks applied before any test run.

A patch that does not parse is never worth spending a test run on, so every
candidate goes through:

  0. no-op          the diff has no semantic content — the model reformatted
                    or re-indented the lines it was told to change without
                    altering behaviour. Such a patch applies cleanly, compiles,
                    passes pyflakes and then fails every FAIL_TO_PASS test.
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
    # Advisory only — never turns ``ok`` false. Surfaced to the coder and
    # recorded in meta.json so a risky-but-passing patch is still visible.
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "changed_files": self.changed_files,
            "added_lines": self.added_lines,
            "removed_lines": self.removed_lines,
            "warnings": self.warnings,
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


# Two diff sides that are equal after normalisation cannot change behaviour.
# Whitespace is the common case (re-indentation, quote tidying, trailing
# spaces), but comment-only edits are caught by the same comparison because
# the code tokens are unchanged.
_WS_RE = re.compile(r"\s+")


def _normalise_line(line: str) -> str:
    return _WS_RE.sub("", line)


def _strip_comments(lines: list[str]) -> list[str]:
    """Drop pure-comment / blank content, using the text after ``#``."""
    out = []
    for line in lines:
        stripped = line.split("#", 1)[0]
        if stripped.strip():
            out.append(stripped)
    return out


def is_semantic_noop(patch: str) -> bool:
    """True when the diff cannot change runtime behaviour.

    Compares the removed and added sides of every hunk, ignoring whitespace
    and comments. A patch where both sides reduce to the same non-empty
    content is a pure reformat: it applies and compiles perfectly and then
    leaves the failing tests exactly as failing as before, so it should never
    be submitted.
    """
    removed: list[str] = []
    added: list[str] = []
    for line in (patch or "").splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added.append(line[1:])
        elif line.startswith("-"):
            removed.append(line[1:])

    if not added and not removed:
        return True

    # Textual comparison first (cheap and exact), then whitespace-insensitive.
    if added == removed:
        return True

    return [ _normalise_line(x) for x in _strip_comments(added) ] == [
        _normalise_line(x) for x in _strip_comments(removed)
    ]


def noop_gate(patch: str) -> GateResult:
    """Reject patches whose only effect is reformatting the target lines."""
    added, removed = diff_stats(patch)
    result = GateResult(
        ok=not is_semantic_noop(patch),
        changed_files=changed_files(patch),
        added_lines=added,
        removed_lines=removed,
    )
    if not result.ok:
        result.errors.append(
            "no-op patch: the diff only reformats the lines it touches "
            "(identical code on both sides once whitespace and comments are "
            "ignored) — it cannot fix anything, so change the actual logic"
        )
    return result


# ── Unresolvable imports ────────────────────────────────────────────────────
# pyflakes cannot see whether an imported module actually exists: a patch that
# adds ``import pmxbot`` to pytest compiles, passes pyflakes, applies cleanly,
# and only dies at harness time when the container does ``import pmxbot``.
# That class of hallucination is cheap to catch up front: a new import is
# resolvable when its top-level name is stdlib, present in the checkout tree,
# or referenced by an import line anywhere in the checkout source (third-party
# deps like numpy are always referenced).  Anything else is fabricated.
_NEW_IMPORT_RE = re.compile(
    r"^\s*(?:import\s+([A-Za-z_][A-Za-z0-9_.]*)|from\s+([A-Za-z_][A-Za-z0-9_.]*)\s+import)"
)
_vocab_cache: dict[str, tuple[set[str], set[str]]] = {}


def _new_top_level_imports(patch: str) -> set[str]:
    names: set[str] = set()
    for line in (patch or "").splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        m = _NEW_IMPORT_RE.match(line[1:])
        if m:
            top = (m.group(1) or m.group(2)).split(".")[0]
            if top and top != "__future__":
                names.add(top)
    return names


def _checkout_vocab(baseline_repo: str) -> tuple[set[str], set[str]]:
    """(top-level names in the tree, names referenced by import lines)."""
    key = str(baseline_repo)
    if key in _vocab_cache:
        return _vocab_cache[key]
    top: set[str] = set()
    referenced: set[str] = set()
    root = Path(baseline_repo)
    for p in root.iterdir():
        if p.name.startswith(".") or p.name.startswith("__pycache__"):
            continue
        top.add(p.name)
    seen_import_files = 0
    for p in root.rglob("*.py"):
        if any(part.startswith(".") or part == "__pycache__" for part in p.parts[len(root.parts):]):
            continue
        seen_import_files += 1
        if seen_import_files > 20000:
            break
        try:
            with p.open(encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    m = _NEW_IMPORT_RE.match(line)
                    if m:
                        referenced.add((m.group(1) or m.group(2)).split(".")[0])
        except OSError:
            continue
    result = (top, referenced)
    _vocab_cache[key] = result
    return result


def unresolvable_imports(baseline_repo: str, patch: str) -> list[str]:
    """New imports the patch adds that cannot exist in this environment."""
    if not baseline_repo or not (patch or "").strip():
        return []
    top, referenced = _checkout_vocab(baseline_repo)
    bad: list[str] = []
    for name in sorted(_new_top_level_imports(patch)):
        if name in sys.stdlib_module_names:
            continue
        if name in top or name in referenced:
            continue
        bad.append(name)
    return bad


# ── Regression risk ─────────────────────────────────────────────────────────
# A patch that rewrites most of a function's body is the shape that produced
# the astropy-12907 regression: the right file, a plausible-looking fix, and
# 6 previously-passing tests turned red. Signature checks cannot see this
# (the signature was unchanged), and in bench mode no test runs locally, so
# the only cheap signal left is *how much* of the function was replaced.
_DEF_LINE_RE = re.compile(r"^\s*(?:async\s+)?(?:def|class)\s+\w+")
_REWRITE_WARN = 0.6   # replace >=60% of a function's body to warn
_REWRITE_MIN_LINES = 8  # ignore trivial functions; rewriting 3 lines is not risky


def _enclosing_functions(lines: list[str], target: set[int]) -> dict[str, set[int]]:
    """Map each function name to the 1-based line numbers it spans."""
    spans: list[tuple[str, int, int]] = []
    for i, line in enumerate(lines):
        if not _DEF_LINE_RE.match(line):
            continue
        indent = len(line) - len(line.lstrip())
        end = len(lines)
        for j in range(i + 1, len(lines)):
            if not lines[j].strip():
                continue
            other = lines[j]
            if len(other) - len(other.lstrip()) <= indent:
                end = j
                break
        name = re.search(r"(?:def|class)\s+(\w+)", line)
        spans.append((name.group(1) if name else f"<anon{i}>", i + 1, end))

    out: dict[str, set[int]] = {}
    for name, start, end in spans:
        body = set(range(start + 1, end + 1))  # exclude the def line itself
        if body & target:
            out[name] = body
    return out


def _hunk_touched_lines(patch: str) -> dict[str, set[int]]:
    """Per-file 1-based NEW-file line numbers the diff adds or removes.

    A unified diff walks the *new* file. A ``-`` line still occupies a line
    number (it is deleted from the new file but exists in the old one), so it
    must advance the cursor or every following line is under-counted. Getting
    this wrong made a whole-function rewrite look like a two-line change.
    """
    touched: dict[str, set[int]] = {}
    current: str | None = None
    lineno = 0
    for line in (patch or "").splitlines():
        if line.startswith("+++ b/"):
            current = line[6:].strip()
            touched.setdefault(current, set())
            lineno = 0
            continue
        if line.startswith("+++ /dev/null"):
            current = None
            continue
        if line.startswith("---") or line.startswith("diff --git") or line.startswith("index "):
            continue
        if current is None:
            continue
        if line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            lineno = int(match.group(1)) - 1 if match else 0
            continue
        if line.startswith("+"):
            lineno += 1
            touched[current].add(lineno)
        elif line.startswith("-"):
            # A deleted line still occupies its position in the new file's
            # numbering, so consecutive removals are consecutive numbers —
            # clamping to the cursor collapsed them into one.
            lineno += 1
            touched[current].add(lineno)
        elif line.startswith(" ") or not line.strip():
            lineno += 1
    return touched


def rewrite_risk(repo_path: str, patch: str) -> list[str]:
    """Warn when a patch replaces most of a function's body.

    Advisory, never fatal: some legitimate fixes *are* large rewrites, so this
    is surfaced to the coder and recorded rather than used to reject a
    candidate outright.
    """
    touched = _hunk_touched_lines(patch)
    if not touched:
        return []

    warnings: list[str] = []
    for rel, lines_changed in touched.items():
        if not lines_changed:
            continue
        target = Path(repo_path) / rel
        try:
            lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue  # deleted file or sandbox-only path
        if not lines:
            continue
        for name, body in _enclosing_functions(lines, lines_changed).items():
            if len(body) < _REWRITE_MIN_LINES:
                continue
            ratio = len(body & lines_changed) / len(body)
            if ratio >= _REWRITE_WARN:
                warnings.append(
                    f"rewrite risk: '{name}' in '{rel}' — the diff replaces "
                    f"{len(body & lines_changed)}/{len(body)} of its body "
                    f"({ratio:.0%}). A broad rewrite of one function is the "
                    f"shape that silently breaks tests that used to pass; "
                    f"prefer the smallest change that fixes the issue."
                )
    return warnings


def noop_gate_with_risk(repo_path: str, patch: str) -> GateResult:
    """No-op rejection plus advisory rewrite warnings."""
    result = noop_gate(patch)
    if not result.ok:
        return result
    result.warnings = rewrite_risk(repo_path, patch)
    return result


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

    # Gate 0 — pure reformat. Runs before any subprocess work.
    noop = noop_gate_with_risk(str(root), patch)
    if not noop.ok:
        return noop
    result.warnings = noop.warnings

    # Gate 0.5 — fabricated module. Runs before any subprocess work.
    if baseline_repo:
        for name in unresolvable_imports(baseline_repo, patch):
            result.errors.append(
                f"unresolvable import '{name}': that module does not exist in "
                f"this repository or in the standard library — do not import "
                f"modules that are not already part of the codebase"
            )

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
