"""
ISHA Offline Brain — Deterministic planner/coder used when no LLM keys.

Enabled automatically when GOOGLE_API_KEY / GROQ_API_KEY are absent so
the full pipeline stays runnable offline (demo + CI). With keys present
the real Gemini/Groq models take over; this module is never called.
"""

import difflib
import re
from pathlib import Path

SECTION_RE = re.compile(
    r"^(BUG REPORT|REPOSITORY CONTEXT|FIX PLAN|TARGET FILE CONTEXT|STRATEGY|"
    r"RETRY INDEX|REPO PATH|PREVIOUS ATTEMPT FAILED):[ \t]*(.*)$",
    re.M,
)

_OPERATOR_CANDIDATES = {
    "+": ["-", "*", "/"],
    "-": ["+", "*", "/"],
    "*": ["+", "-", "/"],
    "/": ["*", "+", "-"],
}

def _param_names(def_line: str) -> list:
    """Parameter names of a ``def`` line, minus ``self``/``cls``.

    ``def percentage(self, value: float) -> float:`` → ``['value']``
    """
    if "(" not in def_line:
        return []
    inner = def_line.split("(", 1)[1].rsplit(")", 1)[0]
    names = []
    for part in inner.split(","):
        part = part.strip()
        if not part or part in ("self", "cls") or part.startswith("*"):
            continue
        name = re.split(r"[:=]", part, 1)[0].strip()
        if name:
            names.append(name)
    return names


def _zero_guard(params: list) -> str | None:
    """Zero-division guard built from the function's real parameters.

    Hardcoding ``b`` would raise NameError inside functions that don't
    have a ``b`` (e.g. ``percentage(value)``), breaking passing tests.
    """
    if len(params) < 2:
        return None
    second = params[1]
    return f'    if {second} == 0:\n        raise ValueError("Cannot divide by zero")\n'


def _type_guard(params: list) -> str | None:
    """Type guard built from the function's real parameters."""
    if not params:
        return None
    checks = " or ".join(f"not isinstance({p}, (int, float))" for p in params[:2])
    return f'    if {checks}:\n        raise TypeError("operands must be numbers")\n'


def _sections(prompt: str) -> dict:
    """Split the standard node prompt into named sections."""
    matches = list(SECTION_RE.finditer(prompt))
    out = {}
    for i, match in enumerate(matches):
        inline = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(prompt)
        block = prompt[start:end].strip()
        out[match.group(1)] = inline if inline else block
    return out


# ---------------------------------------------------------------------- #
# Planner
# ---------------------------------------------------------------------- #

def offline_planner(prompt: str) -> str:
    """Rule-based 2-step fix plan derived from the issue + repo map."""
    secs = _sections(prompt)
    issue = secs.get("BUG REPORT", "")
    context = secs.get("REPOSITORY CONTEXT", "")
    func, file_path = _locate_target(issue, context, secs.get("REPO PATH", ""))

    root_cause = _root_cause(issue, func)
    if func:
        change = (
            f"Step 2: Edit {file_path or '<repo>'} — in {func}(), apply: {root_cause['fix']}"
        )
    else:
        change = "Step 2: Locate the offending function named in the report and correct its logic."
    return f"Step 1: Root cause — {root_cause['why']}\n{change}"


def _root_cause(issue: str, func: str | None) -> dict:
    text = issue.lower()
    where = f"{func}()" if func else "the reported function"
    if "zero" in text or "division by zero" in text:
        return {
            "why": f"{where} performs the division without guarding b == 0, "
            "so ZeroDivisionError escapes instead of a clear ValueError.",
            "fix": "raise ValueError('Cannot divide by zero') when b == 0 before dividing.",
        }
    if any(k in text for k in ("type", "validate", "validation", "string", "non-numeric")):
        return {
            "why": f"{where} does not validate operand types before computing.",
            "fix": "raise TypeError when either operand is not an int/float.",
        }
    if any(
        k in text
        for k in ("denominator", "missing parameter", "missing argument",
                  "signature", "call site", "callers", "accepts only")
    ):
        return {
            "why": f"{where} is missing a parameter its callers need to supply, "
                   "so it computes against a hard-coded value instead of the "
                   "caller's input.",
            "fix": "add the missing parameter to the signature and update every "
                   "caller to pass it (definition and call sites in one patch).",
        }
    if any(k in text for k in ("wrong", "instead of", "incorrect", "returns", "minus", "-")):
        return {
            "why": f"{where} computes the wrong expression — the arithmetic operator "
            "does not match the documented behaviour in the report.",
            "fix": "replace the return expression with the operator the report expects.",
        }
    return {
        "why": f"{where} does not match the behaviour described in the report.",
        "fix": "make the return value match the documented behaviour.",
    }


def offline_regressor(prompt: str) -> str:
    """Rule-based pytest reproduction test for the reported bug."""
    secs = _sections(prompt)
    issue = secs.get("BUG REPORT", "")
    context = secs.get("REPOSITORY CONTEXT", "")
    func, _ = _locate_target(issue, context, secs.get("REPO PATH", ""))
    func = func or "calculate"
    text = issue.lower()

    if "zero" in text:
        return (
            "import pytest\n\n"
            "from calculator import Calculator\n\n\n"
            "def test_repro_reports_bug():\n"
            '    """Reproduces the reported bug: must pass only after the fix."""\n'
            "    with pytest.raises(ValueError, match='Cannot divide by zero'):\n"
            f"        Calculator().{func}(10, 0)\n"
        )
    if any(k in text for k in ("type", "validate", "validation")):
        return (
            "import pytest\n\n"
            "from calculator import Calculator\n\n\n"
            "def test_repro_reports_bug():\n"
            '    """Reproduces the reported bug: must pass only after the fix."""\n'
            "    with pytest.raises(TypeError):\n"
            f'        Calculator().{func}("two", 2)\n'
        )
    return (
        "from calculator import Calculator\n\n\n"
        "def test_repro_reports_bug():\n"
        '    """Reproduces the reported bug: must pass only after the fix."""\n'
        "    calc = Calculator()\n"
        f"    assert calc.{func}(5, 3) == 2\n"
    )


# ---------------------------------------------------------------------- #
# Coder
# ---------------------------------------------------------------------- #

def offline_coder(prompt: str) -> str:
    """Deterministic unified diff. Candidate edits advance with RETRY INDEX."""
    secs = _sections(prompt)
    issue = secs.get("BUG REPORT", "")
    context = secs.get("TARGET FILE CONTEXT") or secs.get("REPOSITORY CONTEXT", "")
    func, _ = _locate_target(issue, context, secs.get("REPO PATH", ""))
    repo_path = secs.get("REPO PATH", "")
    try:
        retry_index = int(secs.get("RETRY INDEX", "0") or 0)
    except ValueError:
        retry_index = 0

    if not func or not repo_path:
        return "[CODER ERROR] offline coder could not locate target function"

    target = _find_file(repo_path, func)
    if target is None:
        return f"[CODER ERROR] no file defines {func}() under {repo_path}"

    original = target.read_text(encoding="utf-8", errors="replace")
    updated = _rewrite(original, func, issue, retry_index)
    if updated is None or updated == original:
        return "[CODER ERROR] offline coder exhausted candidate edits"

    rel = target.name
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        updated.splitlines(keepends=True),
        fromfile=f"a/{rel}",
        tofile=f"b/{rel}",
    )
    return "".join(diff)


def _indent_block(block: str, indent: int) -> list:
    """Re-indent a 4-space-indented template block to `indent` columns."""
    pad = " " * indent
    out = []
    for line in block.splitlines(keepends=True):
        out.append(pad + (line[4:] if line.startswith("    ") else line))
    return out


def _insert_point(body: list) -> int:
    """Index in `body` right after the def line and its docstring."""
    index = 1
    if index < len(body):
        stripped = body[index].lstrip()
        if stripped.startswith(('"""', "'''")):
            quote = stripped[:3]
            if not (len(stripped) > 3 and stripped.count(quote) >= 2):
                index += 1
                while index < len(body) and quote not in body[index]:
                    index += 1
            index += 1
    while index < len(body) and (not body[index].strip() or body[index].lstrip().startswith("#")):
        index += 1
    return min(index, len(body))


def _rewrite(content: str, func: str, issue: str, retry_index: int) -> str | None:
    lines = content.splitlines(keepends=True)
    text = issue.lower()

    start = None
    for i, line in enumerate(lines):
        if re.match(rf"^\s*def\s+{re.escape(func)}\s*\(", line):
            start = i
            break
    if start is None:
        return None

    base_indent = len(lines[start]) - len(lines[start].lstrip())
    end = len(lines)
    for j in range(start + 1, len(lines)):
        line = lines[j]
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= base_indent and re.match(r"^\s*(def|class|@)", line):
            end = j
            break

    body = lines[start:end]
    guard_at = _insert_point(body)
    params = _param_names(lines[start])

    if "zero" in text and any("/" in ln for ln in body):
        guard = _zero_guard(params)
        if guard is None or any(
            re.search(r"^\s*raise\s+ValueError", ln) for ln in body
        ):
            return None
        patched = list(body)
        patched[guard_at:guard_at] = _indent_block(guard, base_indent + 4)
        lines[start:end] = patched
        return "".join(lines)

    if any(k in text for k in ("type", "validate", "validation")):
        guard = _type_guard(params)
        if guard is None or any(
            re.search(r"^\s*raise\s+TypeError", ln) for ln in body
        ):
            return None
        patched = list(body)
        patched[guard_at:guard_at] = _indent_block(guard, base_indent + 4)
        lines[start:end] = patched
        return "".join(lines)

    # Arithmetic-operator ladder: each retry tries the next candidate.
    for offset, line in enumerate(body):
        match = re.search(r"^(\s*return\s+)([A-Za-z_]\w*)\s*([+\-*/])\s*([A-Za-z_]\w*)", line)
        if not match:
            continue
        op = match.group(3)
        candidates = _OPERATOR_CANDIDATES.get(op, [])
        if not candidates:
            return None
        candidate = candidates[retry_index % len(candidates)]
        newline = (
            f"{match.group(1)}{match.group(2)} {candidate} {match.group(4)}"
            f"{line[match.end():]}"
        )
        patched = list(body)
        patched[offset] = newline if newline.endswith("\n") else newline + "\n"
        lines[start:end] = patched
        return "".join(lines)

    return None


def _locate_target(issue: str, context: str, repo_path: str) -> tuple:
    """Find (function_name, file_path) for the reported bug."""
    words = set(re.findall(r"[a-z_][a-z0-9_]*", issue.lower()))
    # Test functions describe the symptom; the target lives in the source module.
    names = re.findall(r"def\s+(\w+)\s*\(", context)
    # AST map entries look like "    subtract(self, a: float, b: float)".
    names += re.findall(r"^\s{2,}(\w+)\s*\([^)]*\)\s*$", context, re.M)
    candidates = [n for n in dict.fromkeys(names) if not n.startswith("test_")]
    if repo_path:
        # Keep only names that resolve to a non-test source file.
        candidates = [n for n in candidates if _find_file(repo_path, n) is not None]

    func = None
    for name in candidates:
        if name.lower() in words:
            func = name
            break
    if func is None:
        for name in candidates:
            if name.lower() in ("subtract", "divide", "add", "multiply"):
                func = name
                break
    if func is None and candidates:
        func = candidates[0]

    file_path = None
    if func and repo_path:
        found = _find_file(repo_path, func)
        if found is not None:
            file_path = found.name
    if file_path is None:
        match = re.search(r"([\w./\\-]+\.py)", context)
        file_path = match.group(1) if match else None
    return func, file_path


def _find_file(repo_path: str, func: str) -> Path | None:
    root = Path(repo_path)
    if not root.exists():
        return None
    for path in sorted(root.rglob("*.py")):
        if any(part in {"__pycache__", ".git", "venv", ".venv"} for part in path.parts):
            continue
        if path.name.startswith(("test_", "conftest")):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if re.search(rf"def\s+{re.escape(func)}\s*\(", content):
            return path
    return None
