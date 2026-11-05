"""
ISHA Git History Reasoning — why the code is the way it is.

Before patching, surfaces `git log -p` for the files the fix will touch so
the planner and coder know whether the current shape of the code is the
result of an earlier bugfix. Changing such code carelessly can reintroduce
the old problem the history was written to prevent.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_FILE_RE = re.compile(r"[\w./\\-]+\.py\b")


def mentioned_files(text: str, limit: int = 5) -> list[str]:
    """Distinct .py file references in a plan/issue, in order of appearance."""
    if not text:
        return []
    seen: list[str] = []
    for match in _FILE_RE.finditer(text):
        candidate = match.group(0).lstrip("./")
        if candidate not in seen:
            seen.append(candidate)
        if len(seen) >= limit:
            break
    return seen


def file_history(
    repo_path: str,
    rel_files: list[str],
    max_commits: int = 3,
    per_file_chars: int = 900,
    total_chars: int = 2600,
) -> str:
    """`git log -p` summary for each file; empty string when unavailable.

    Degrades silently on non-git repos, shallow checkouts, or timeouts.
    """
    if not repo_path or not rel_files:
        return ""
    root = Path(repo_path)
    if not root.exists():
        return ""

    sections: list[str] = []
    budget = total_chars
    for rel in rel_files:
        if budget <= 0:
            break
        try:
            proc = subprocess.run(
                [
                    "git", "-C", str(root), "log",
                    f"-n{max_commits}",
                    "--date=short",
                    "--format=COMMIT %h %ad %an%n%s%n",
                    "-p", "--unified=1", "--", rel,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
        except Exception:
            continue
        out = (proc.stdout or "").strip()
        if not out:
            continue
        if len(out) > per_file_chars:
            out = out[:per_file_chars] + "\n...[history truncated]"
        out = out[:budget]
        sections.append(f"### {rel}\n{out}")
        budget -= len(out)

    return "\n\n".join(sections)
