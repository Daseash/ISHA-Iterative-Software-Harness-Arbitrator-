"""
ISHA Patch Engine — Apply unified diffs with git, then manual fallback.

Supports:
  * Unified diffs applied via `git apply --3way` and `git apply`
  * Robust manual hunk application with exact and fuzzy whitespace matching
  * SEARCH/REPLACE blocks with fuzzy whitespace tolerance
  * Line ending preservation (CRLF on Windows vs LF on Linux)
  * Patch validation via `git apply --check`
  * Apply failure classification and recording for Stage B reporting
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path

_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _run(args: list, cwd: str, text: str, timeout: int = 60) -> tuple[bool, str]:
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


def apply_patch(repo_path: str, diff_text: str) -> tuple[bool, str]:
    """Apply a unified diff patch or SEARCH/REPLACE block. Returns (success: bool, message: str)."""
    if not diff_text or not diff_text.strip():
        return False, "Empty patch"

    root = Path(repo_path)
    if not root.exists():
        return False, f"Repo path does not exist: {repo_path}"

    # 0) If SEARCH/REPLACE markers are detected, try search/replace first
    if "<<<<<<< SEARCH" in diff_text or "<<<< SEARCH" in diff_text:
        ok_sr, msg_sr = _apply_search_replace(root, diff_text)
        if ok_sr:
            return True, msg_sr

    diff = _normalize(diff_text)
    msg = ""
    # 1) git apply --3way (best fidelity inside a git repo)
    if (root / ".git").exists():
        ok, msg = _run(["git", "apply", "--3way", "--whitespace=nowarn", "-"], str(root), diff)
        if not ok:
            ok, msg2 = _run(["git", "apply", "--whitespace=nowarn", "-"], str(root), diff)
            msg = f"{msg}\n{msg2}"
        if ok:
            return True, "Applied via git apply --3way"

    # 2) Manual unified-diff hunk application with line-ending preservation
    msg_m = ""
    try:
        ok_m, msg_m = _apply_manual(root, diff)
        if ok_m:
            return True, msg_m
    except Exception as exc:
        msg_m = f"Manual apply failed: {exc}"

    # 3) Fallback: try SEARCH/REPLACE parser if not tried already
    ok_sr, msg_sr = _apply_search_replace(root, diff_text)
    if ok_sr:
        return True, msg_sr

    return False, f"{msg_m} (git: {msg}; sr: {msg_sr})"


def validate_patch(repo_path: str, diff_text: str) -> tuple[bool, str]:
    """Validate patch on a clean checkout using git apply --check --whitespace=nowarn."""
    if not diff_text or not diff_text.strip():
        return False, "Empty patch"
    root = Path(repo_path)
    if not (root / ".git").exists():
        return True, "Not a git repo, skipping git apply --check"
    diff = _normalize(diff_text)
    ok, msg = _run(["git", "apply", "--check", "--whitespace=nowarn", "-"], str(root), diff)
    return ok, msg


def classify_apply_failure(error_msg: str, diff_text: str = "") -> str:
    """Classify apply failure into {context_mismatch, whitespace, wrong_path, line_endings, malformed_hunk}."""
    err = (error_msg or "").lower()
    if any(h in err for h in ("corrupt patch", "malformed", "patch fragment without header", "fatal: git diff header")):
        return "malformed_hunk"
    if any(h in err for h in ("no such file", "does not exist", "missing file", "unrecognized file path")):
        return "wrong_path"
    if any(h in err for h in ("trailing whitespace", "whitespace error")):
        return "whitespace"
    if any(h in err for h in ("carriage return", "crlf", "\\r", "line ending")):
        return "line_endings"
    return "context_mismatch"


def record_apply_failure(
    instance_id: str,
    candidate_idx: int,
    round_idx: int,
    patch_text: str,
    error_msg: str,
) -> str:
    """Save failing patch and error to results/apply_failures/ and update summary.json."""
    failures_dir = Path(__file__).resolve().parents[2] / "results" / "apply_failures"
    failures_dir.mkdir(parents=True, exist_ok=True)

    cause = classify_apply_failure(error_msg, patch_text)
    slug = (instance_id or "unknown").replace("/", "__")
    base_name = f"{slug}_c{candidate_idx}_round{round_idx}"

    try:
        (failures_dir / f"{base_name}.patch").write_text(patch_text or "", encoding="utf-8")
        (failures_dir / f"{base_name}.json").write_text(
            json.dumps({
                "instance_id": instance_id,
                "candidate": candidate_idx,
                "round": round_idx,
                "error": error_msg,
                "cause": cause,
                "timestamp": time.time(),
            }, indent=2),
            encoding="utf-8",
        )

        summary_path = failures_dir / "summary.json"
        summary = {}
        if summary_path.is_file():
            try:
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
            except Exception:
                summary = {}
        summary[cause] = summary.get(cause, 0) + 1
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    except Exception:
        pass
    return cause


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


def _split_files(diff: str) -> list[dict]:
    """Split a multi-file diff into per-file (path, hunks) records."""
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


def _apply_manual(root: Path, diff: str) -> tuple[bool, str]:
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

        raw_bytes = target.read_bytes()
        is_crlf = b"\r\n" in raw_bytes
        newline = "\r\n" if is_crlf else "\n"

        original = raw_bytes.decode("utf-8", errors="replace").splitlines(keepends=True)
        updated = list(original)
        failed = False
        for hunk in record["hunks"]:
            ok, updated = _apply_hunk(updated, hunk, newline=newline)
            if not ok:
                errors.append(
                    f"Hunk failed in {rel}: {hunk[0]} — expected context "
                    f"not found in file: {_context_preview(hunk)}"
                )
                failed = True
                break
        if not failed:
            target.write_bytes("".join(updated).encode("utf-8"))
            applied.append(rel)

    if applied:
        suffix = f"; warnings: {'; '.join(errors)}" if errors else ""
        return True, f"Applied patch to: {', '.join(applied)}{suffix}"
    return False, "; ".join(errors) or "No hunks applied"


def _apply_search_replace(root: Path, text: str) -> tuple[bool, str]:
    """Parse and apply SEARCH/REPLACE blocks with exact and fuzzy matching."""
    lines = text.splitlines()
    blocks = []
    current_file = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        file_m = re.match(r"^(?:###?\s*)?(?:File:\s*|Path:\s*|--- a/|\+\+\+ b/)?([a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9_]+)", line)
        if file_m and not line.startswith("<<<<"):
            cand_p = file_m.group(1).replace("\\", "/")
            if (root / cand_p).is_file():
                current_file = cand_p

        if line.startswith("<<<<<<< SEARCH") or line.startswith("<<<< SEARCH"):
            search_lines = []
            replace_lines = []
            i += 1
            while i < len(lines) and not (lines[i].strip().startswith("=======") or lines[i].strip().startswith("====")):
                search_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            while i < len(lines) and not (lines[i].strip().startswith(">>>>>>> REPLACE") or lines[i].strip().startswith(">>>> REPLACE")):
                replace_lines.append(lines[i])
                i += 1
            blocks.append({
                "file": current_file,
                "search": search_lines,
                "replace": replace_lines,
            })
        i += 1

    if not blocks:
        return False, "No SEARCH/REPLACE blocks found"

    applied = []
    errors = []
    for b in blocks:
        rel = b["file"]
        search_lines = b["search"]
        replace_lines = b["replace"]

        target = None
        if rel and (root / rel).is_file():
            target = root / rel
        else:
            search_exact = "\n".join(search_lines)
            candidates = []
            for p in root.rglob("*.py"):
                if not p.is_file() or any(ign in p.parts for ign in (".git", "venv", ".venv", "__pycache__")):
                    continue
                try:
                    txt = p.read_text(encoding="utf-8", errors="replace")
                    if search_exact and search_exact in txt:
                        candidates.append(p)
                except Exception:
                    pass
            if len(candidates) == 1:
                target = candidates[0]
                rel = str(target.relative_to(root)).replace("\\", "/")

        if not target or not target.is_file():
            errors.append(f"Target file not found for block (hint: {rel})")
            continue

        raw_bytes = target.read_bytes()
        is_crlf = b"\r\n" in raw_bytes
        newline = "\r\n" if is_crlf else "\n"
        file_lines = raw_bytes.decode("utf-8", errors="replace").splitlines(keepends=True)
        stripped_file = [ln.rstrip("\r\n") for ln in file_lines]
        stripped_search = [ln.rstrip("\r\n") for ln in search_lines]

        idx = _locate(stripped_file, stripped_search, 0)
        if idx is None:
            idx = _locate_fuzzy(stripped_file, stripped_search, 0)

        if idx is not None:
            new_lines = [f"{line}{newline}" for line in replace_lines]
            file_lines[idx : idx + len(stripped_search)] = new_lines
            target.write_bytes("".join(file_lines).encode("utf-8"))
            applied.append(rel)
        else:
            errors.append(f"Search block not found in {rel}")

    if applied:
        return True, f"Applied SEARCH/REPLACE to: {', '.join(set(applied))}"
    return False, "; ".join(errors) or "Failed to apply SEARCH/REPLACE blocks"


def _context_preview(hunk: list) -> str:
    """First context/removal line of a hunk — the line that failed to match."""
    for line in hunk[1:]:
        if line[:1] in (" ", "-"):
            return repr(line[1:][:120])
    return repr(hunk[0][:120])


def _apply_hunk(lines: list, hunk: list, newline: str = "\n") -> tuple[bool, list]:
    header = _HUNK_RE.match(hunk[0])
    start = int(header.group(1)) - 1 if header else 0

    body = [ln.rstrip("\r\n") for ln in hunk[1:] if not ln.startswith("\\")]
    old_block = [ln[1:] for ln in body if ln[:1] in (" ", "-")]
    new_block = [ln[1:] for ln in body if ln[:1] in (" ", "+")]
    if not old_block:
        return False, lines

    idx = _locate(lines, old_block, start)
    if idx is None:
        idx = _locate_fuzzy(lines, old_block, start)
    if idx is not None:
        lines[idx : idx + len(old_block)] = [f"{line}{newline}" for line in new_block]
        return True, lines

    if _apply_body(lines, body, start, newline=newline):
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


def _apply_body(lines: list, body: list, start: int, newline: str = "\n") -> bool:
    """Apply a hunk operation-by-operation when the full block will not match."""
    ops = _body_ops(body)
    if not ops:
        return False
    pos = start if 0 <= start < len(lines) else 0
    anchored = False
    changed = 0
    for kind, old, new in ops:
        if kind == "keep":
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
            lines[idx : idx + len(old)] = [f"{line}{newline}" for line in new]
            pos = idx + len(new)
            anchored = True
            changed += 1
            continue
        if 0 < pos <= len(lines):
            lines[pos:pos] = [f"{line}{newline}" for line in new]
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
