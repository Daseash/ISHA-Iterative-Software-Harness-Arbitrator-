"""
ISHA Patch Engine — Apply unified diffs with git, then manual fallback.

Tries `git apply --3way` first (works inside a git worktree) and falls
back to a hand-rolled hunk applier so patches land in plain copies too.
"""

import re
import subprocess
from pathlib import Path

_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _run(args: list, cwd: str, text: str, timeout: int = 60) -> tuple:
    try:
        proc = subprocess.run(
            args,
            cwd=cwd,
            input=text,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode == 0, (proc.stdout + proc.stderr).strip()
    except Exception as exc:
        return False, str(exc)


def apply_patch(repo_path: str, diff_text: str) -> tuple:
    """Apply a unified diff patch. Returns (success: bool, message: str)."""
    if not diff_text or not diff_text.strip():
        return False, "Empty patch"

    diff = _normalize(diff_text)
    root = Path(repo_path)
    if not root.exists():
        return False, f"Repo path does not exist: {repo_path}"

    msg = ""
    # 1) git apply --3way (best fidelity inside a git repo)
    if (root / ".git").exists():
        ok, msg = _run(["git", "apply", "--3way", "--whitespace=nowarn", "-"], str(root), diff)
        if not ok:
            ok, msg2 = _run(["git", "apply", "--whitespace=nowarn", "-"], str(root), diff)
            msg = f"{msg}\n{msg2}"
        if ok:
            return True, "Applied via git apply --3way"

    # 2) Manual unified-diff hunk application
    try:
        return _apply_manual(root, diff)
    except Exception as exc:
        return False, f"Manual apply failed: {exc} (git: {msg})"


def _normalize(diff_text: str) -> str:
    """Strip markdown fences and keep only the diff body."""
    text = diff_text.strip()
    if "```" in text:
        blocks = re.findall(r"```(?:diff|patch)?\n(.*?)```", text, flags=re.S)
        if blocks:
            text = max(blocks, key=len).strip()
    if "diff --git" in text:
        text = text[text.index("diff --git"):]
    return text.rstrip() + "\n"


def _split_files(diff: str) -> list:
    """Split a multi-file diff into per-file (path, hunks) records.

    Handles both ``diff --git`` headers and plain ``--- a/x`` / ``+++ b/x``
    pairs: a plain ``---`` while a record is already open starts a NEW file,
    otherwise every hunk after the first would be applied to the wrong file.
    A ``---`` line is only treated as a header when the next line is ``+++``,
    so a removed line whose content starts with ``--`` can't split a hunk.
    """
    raw = diff.splitlines()
    files = []
    current = None

    def _new_record():
        return {"old": None, "new": None, "hunks": []}

    i = 0
    while i < len(raw):
        line = raw[i]
        if line.startswith("diff --git "):
            if current:
                files.append(current)
            current = _new_record()
            for token in line.split()[2:]:
                if token.startswith("a/"):
                    current["old"] = token[2:]
                elif token.startswith("b/"):
                    current["new"] = token[2:]
        elif line.startswith("--- ") and i + 1 < len(raw) and raw[i + 1].startswith("+++ "):
            if current is None:
                current = _new_record()
            elif current["hunks"]:
                files.append(current)
                current = _new_record()
            path = line[4:].strip()
            current["old"] = path[2:] if path.startswith("a/") else path
        elif line.startswith("+++ "):
            if current is None:
                current = _new_record()
            path = line[4:].strip()
            if path != "/dev/null":
                current["new"] = path[2:] if path.startswith("b/") else path
        elif line.startswith("@@"):
            if current is None:
                current = _new_record()
            current["hunks"].append([line])
        elif current is not None and current["hunks"]:
            current["hunks"][-1].append(line)
        i += 1

    if current:
        files.append(current)
    return [f for f in files if f["hunks"]]


def _apply_manual(root: Path, diff: str) -> tuple:
    applied = []
    errors = []
    for record in _split_files(diff):
        rel = record["new"] or record["old"]
        if not rel:
            errors.append("Unrecognized file path in diff")
            continue
        target = root / rel
        if not target.exists():
            if record["old"] and (root / record["old"]).exists():
                target = root / record["old"]
            else:
                errors.append(f"Missing file: {rel}")
                continue

        original = target.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        updated = list(original)
        failed = False
        for hunk in record["hunks"]:
            ok, updated = _apply_hunk(updated, hunk)
            if not ok:
                errors.append(
                    f"Hunk failed in {rel}: {hunk[0]} — expected context "
                    f"not found in file: {_context_preview(hunk)}"
                )
                failed = True
                break
        if not failed:
            target.write_text("".join(updated), encoding="utf-8")
            applied.append(rel)

    if applied:
        suffix = f"; warnings: {'; '.join(errors)}" if errors else ""
        return True, f"Applied patch to: {', '.join(applied)}{suffix}"
    return False, "; ".join(errors) or "No hunks applied"


def _context_preview(hunk: list) -> str:
    """First context/removal line of a hunk — the line that failed to match."""
    for line in hunk[1:]:
        if line[:1] in (" ", "-"):
            return repr(line[1:][:120])
    return repr(hunk[0][:120])


def _apply_hunk(lines: list, hunk: list) -> tuple:
    header = _HUNK_RE.match(hunk[0])
    # LLMs often emit a bare "@@" (or "@@ function signature @@") with no
    # line numbers.  The line number is only a search hint — _locate falls
    # back to scanning the whole file — so a missing header must not fail
    # an otherwise valid hunk.
    start = int(header.group(1)) - 1 if header else 0

    body = [ln.rstrip("\r\n") for ln in hunk[1:] if not ln.startswith("\\")]
    old_block = [ln[1:] for ln in body if ln[:1] in (" ", "-")]
    new_block = [ln[1:] for ln in body if ln[:1] in (" ", "+")]
    if not old_block:
        return False, lines

    # Fast path: the whole hunk matches the file verbatim.
    idx = _locate(lines, old_block, start)
    if idx is None:
        # Indentation drift is the most common reason a hand-written hunk
        # misses; retry on whitespace-normalised content.
        idx = _locate_fuzzy(lines, old_block, start)
    if idx is not None:
        lines[idx : idx + len(old_block)] = [f"{line}\n" for line in new_block]
        return True, lines

    # Slow path: the model restated context it did not copy exactly (a
    # reworded docstring is the usual culprit).  Apply only the lines it
    # actually wants changed and take every unchanged line from the file
    # itself, so the result cannot contain hallucinated text.
    if _apply_body(lines, body, start):
        return True, lines
    return False, lines


def _body_ops(body: list) -> list:
    """Group a hunk body into keep / replace / insert operations."""
    ops: list = []
    i = 0
    while i < len(body):
        ch = body[i][:1]
        if ch == " ":
            ops.append(("keep", [body[i][1:]], []))
            i += 1
        elif ch == "-":
            old: list = []
            new: list = []
            while i < len(body) and body[i][:1] in "-+":
                (old if body[i][:1] == "-" else new).append(body[i][1:])
                i += 1
            ops.append(("replace", old, new))
        elif ch == "+":
            new = []
            while i < len(body) and body[i][:1] == "+":
                new.append(body[i][1:])
                i += 1
            ops.append(("insert", [], new))
        else:
            i += 1
    return ops


def _apply_body(lines: list, body: list, start: int) -> bool:
    """Apply a hunk operation-by-operation when the full block will not match."""
    ops = _body_ops(body)
    if not ops:
        return False
    pos = start if 0 <= start < len(lines) else 0
    anchored = False
    changed = 0
    for kind, old, new in ops:
        if kind == "keep":
            # Context only advances the cursor — it is never written, so a
            # short forward window is enough and cannot drag the cursor to
            # an unrelated part of the file.
            idx = _locate_near(lines, old, pos)
            if idx is not None:
                pos = idx + len(old)
                anchored = True
            continue
        if kind == "replace":
            idx = _locate_near(lines, old, pos, span=200) if anchored else None
            if idx is None:
                idx = _locate(lines, old, pos)
            if idx is None:
                idx = _locate_fuzzy(lines, old, pos)
            if idx is None:
                continue
            lines[idx : idx + len(old)] = [f"{line}\n" for line in new]
            pos = idx + len(new)
            anchored = True
            changed += 1
            continue
        if 0 < pos <= len(lines):
            lines[pos:pos] = [f"{line}\n" for line in new]
            pos += len(new)
            changed += 1
    return changed > 0


def _locate_near(lines: list, content: list, center: int, span: int = 40) -> int | None:
    """Exact-then-whitespace match inside a window around *center*."""
    if not content:
        return None
    n = len(content)
    lo = max(0, center - span)
    hi = min(len(lines) - n + 1, center + span + 1)
    if lo >= hi:
        return None
    want = [c.rstrip("\r\n") for c in content]
    for i in range(lo, hi):
        if [lines[j].rstrip("\r\n") for j in range(i, i + n)] == want:
            return i
    soft = [c.strip() for c in want]
    for i in range(lo, hi):
        if [lines[j].rstrip("\r\n").strip() for j in range(i, i + n)] == soft:
            return i
    return None


def _locate_fuzzy(lines: list, old_block: list, start: int) -> int | None:
    """Whitespace-tolerant fallback used only after an exact match fails."""
    if not old_block:
        return None
    want = [ln.strip() for ln in old_block]
    n = len(want)
    order = list(range(start, len(lines) - n + 1)) + list(range(0, start))
    for i in order:
        if i < 0:
            continue
        current = [lines[j].rstrip("\r\n").strip() for j in range(i, i + n)]
        if current == want:
            return i
    return None


def _locate(lines: list, old_block: list, start: int) -> int | None:
    if not old_block:
        return start if 0 <= start <= len(lines) else None
    if 0 <= start <= len(lines) - len(old_block):
        current = [ln.rstrip("\r\n") for ln in lines[start : start + len(old_block)]]
        if current == old_block:
            return start
    for i in range(0, len(lines) - len(old_block) + 1):
        current = [ln.rstrip("\r\n") for ln in lines[i : i + len(old_block)]]
        if current == old_block:
            return i
    return None
