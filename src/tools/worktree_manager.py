"""
ISHA Worktree Manager — Isolated git worktrees for multi-agent attempts.

Each parallel agent gets its own working directory and branch so agents
never touch each other's files. Repos that aren't git repositories fall
back to a plain directory copy so the pipeline still runs.
"""

import shutil
import subprocess
from pathlib import Path

WORKTREE_ROOT = ".worktrees"
_CREATED: set = set()


def _git(repo_path: str, *args: str, timeout: int = 60) -> tuple:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return proc.returncode == 0, (proc.stdout + proc.stderr).strip()
    except Exception as exc:
        return False, str(exc)


def create_worktree(repo_path: str, name: str) -> str:
    """Create an isolated git worktree for an agent attempt."""
    root = Path(repo_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"repo not found: {repo_path}")

    dest = (root.parent / WORKTREE_ROOT / name).resolve()

    if (root / ".git").exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        branch = f"{name}-fix"
        ok, msg = _git(str(root), "worktree", "add", str(dest), "-b", branch)
        if not ok:
            ok, msg = _git(str(root), "worktree", "add", str(dest), branch)
        if not ok:
            raise RuntimeError(f"git worktree add failed: {msg}")
    else:
        if dest.exists():
            shutil.rmtree(dest, ignore_errors=True)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            root,
            dest,
            ignore=shutil.ignore_patterns(
                "__pycache__", ".git", "*.pyc", "venv", ".venv", "node_modules"
            ),
        )

    _CREATED.add(str(dest))
    return str(dest)


def remove_worktree(worktree_path: str) -> bool:
    """Remove a worktree and its branch after arbitration."""
    if not worktree_path:
        return False
    path = Path(worktree_path)
    if not path.exists():
        return False

    repo_root = path.parent.parent  # ../worktrees/<name> -> repo root
    if (path / ".git").exists() or _is_git_worktree(path):
        ok, _ = _git(str(repo_root), "worktree", "remove", "--force", str(path))
        if not ok:
            shutil.rmtree(path, ignore_errors=True)
        _git(str(repo_root), "branch", "-D", f"{path.name}-fix")
    else:
        shutil.rmtree(path, ignore_errors=True)

    _CREATED.discard(str(path))
    return not path.exists()


def cleanup_all_worktrees(repo_path: str) -> None:
    """Remove all worktrees created by ISHA."""
    root = Path(repo_path).resolve()
    if (root / ".git").exists():
        _, listing = _git(str(root), "worktree", "list", "--porcelain")
        for line in listing.splitlines():
            if line.startswith("worktree "):
                target = Path(line[len("worktree "):].strip())
                if target.name in {Path(p).name for p in list(_CREATED)}:
                    _git(str(root), "worktree", "remove", "--force", str(target))

    for created in list(_CREATED):
        shutil.rmtree(created, ignore_errors=True)
    _CREATED.clear()

    wt_dir = root.parent / WORKTREE_ROOT
    if wt_dir.exists() and not any(wt_dir.iterdir()):
        shutil.rmtree(wt_dir, ignore_errors=True)


def _is_git_worktree(path: Path) -> bool:
    """True when the directory is a linked git worktree (`.git` file)."""
    marker = path / ".git"
    return marker.is_file()


def worktrees_dir(repo_path: str) -> Path:
    """Directory that holds ISHA worktrees for a repo."""
    return Path(repo_path).resolve().parent / WORKTREE_ROOT
