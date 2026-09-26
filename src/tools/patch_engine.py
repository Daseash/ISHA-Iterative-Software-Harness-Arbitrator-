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
    """Split a multi-file diff into per-file (path, hunks) records."""
    files = []
    current = None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            if current:
                files.append(current)
            current = {"old": None, "new": None, "hunks": []}
            for token in line.split()[2:]:
                if token.startswith("a/"):
                    current["old"] = token[2:]
                elif token.startswith("b/"):
                    current["new"] = token[2:]
        elif line.startswith("--- "):
            if current is None:
                current = {"old": None, "new": None, "hunks": []}
            path = line[4:].strip()
            current["old"] = path[2:] if path.startswith("a/") else path
        elif line.startswith("+++ "):
            if current is None:
                current = {"old": None, "new": None, "hunks": []}
            path = line[4:].strip()
            if path != "/dev/null":
                current["new"] = path[2:] if path.startswith("b/") else path
        elif line.startswith("@@"):
            if current is None:
                current = {"old": None, "new": None, "hunks": []}
            current["hunks"].append([line])
        elif current is not None and current["hunks"]:
            current["hunks"][-1].append(line)

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
                errors.append(f"Hunk failed in {rel}: {hunk[0]}")
                failed = True
                break
        if not failed:
            target.write_text("".join(updated), encoding="utf-8")
            applied.append(rel)

    if applied:
        suffix = f"; warnings: {'; '.join(errors)}" if errors else ""
        return True, f"Applied patch to: {', '.join(applied)}{suffix}"
    return False, "; ".join(errors) or "No hunks applied"


def _apply_hunk(lines: list, hunk: list) -> tuple:
    header = _HUNK_RE.match(hunk[0])
    if not header:
        return False, lines
    start = int(header.group(1)) - 1

    body = [ln.rstrip("\r\n") for ln in hunk[1:] if not ln.startswith("\\")]
    old_block = [ln[1:] for ln in body if ln[:1] in (" ", "-")]
    new_block = [ln[1:] for ln in body if ln[:1] in (" ", "+")]

    idx = _locate(lines, old_block, start)
    if idx is None:
        return False, lines

    current = [ln.rstrip("\r\n") for ln in lines[idx : idx + len(old_block)]]
    if current != old_block:
        return False, lines

    lines[idx : idx + len(old_block)] = [f"{line}\n" for line in new_block]
    return True, lines


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
