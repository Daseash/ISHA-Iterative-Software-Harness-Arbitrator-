"""
ISHA Git Manager — Branch creation, rollback, and commit management.

Thin subprocess wrappers used by the sandbox and merger nodes.
"""

import subprocess
from pathlib import Path


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


def create_branch(repo_path: str, branch_name: str) -> bool:
    """Create a new git branch for the fix attempt."""
    if not repo_path or not (Path(repo_path) / ".git").exists():
        return False
    ok, _ = _git(repo_path, "checkout", "-b", branch_name)
    if ok:
        return True
    return _git(repo_path, "checkout", branch_name)[0]


def commit_fix(repo_path: str, message: str) -> bool:
    """Commit the applied patch with a descriptive message."""
    if not repo_path or not (Path(repo_path) / ".git").exists():
        return False
    _git(repo_path, "add", "-A")
    ok, _ = _git(repo_path, "commit", "-m", message)
    if ok:
        return True
    # Nothing staged / nothing to commit is treated as failure.
    return False


def rollback(repo_path: str) -> bool:
    """Rollback to the previous clean state."""
    if not repo_path or not (Path(repo_path) / ".git").exists():
        return False
    ok, _ = _git(repo_path, "checkout", "--", ".")
    _git(repo_path, "clean", "-fd")
    return ok


def clone_repo(github_url: str, target_dir: str) -> str:
    """Clone a GitHub repository to a local directory.

    Used to fetch external repos for ISHA to analyse and patch.
    Returns the target directory path on success.
    """
    subprocess.run(
        ["git", "clone", "--depth", "1", github_url, target_dir],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    return target_dir


def get_current_branch(repo_path: str) -> str:
    """Get the current checked-out branch name."""
    ok, out = _git(repo_path, "rev-parse", "--abbrev-ref", "HEAD")
    return out.strip() if ok else "main"


def get_remote_url(repo_path: str, remote: str = "origin") -> str:
    """Get the URL of the specified remote."""
    ok, out = _git(repo_path, "remote", "get-url", remote)
    return out.strip() if ok else ""


def push_branch(repo_path: str, branch_name: str, remote: str = "origin") -> tuple[bool, str]:
    """Push branch to remote."""
    return _git(repo_path, "push", "-u", remote, branch_name)


def create_pull_request(repo_path: str, title: str, body: str, branch: str = "") -> tuple[bool, str]:
    """Create a pull request using GitHub CLI (gh) if available, GITHUB_TOKEN, or return URL."""
    import os
    import re
    import shutil

    # 1. Try GitHub CLI `gh`
    if shutil.which("gh"):
        cmd = ["gh", "pr", "create", "--title", title, "--body", body]
        if branch:
            cmd += ["--head", branch]
        try:
            proc = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            if proc.returncode == 0:
                return True, proc.stdout.strip()
        except Exception:
            pass

    # 2. Try GITHUB_TOKEN API
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    remote_url = get_remote_url(repo_path)
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", remote_url)
    if token and m:
        owner, repo = m.group(1), m.group(2)
        try:
            import json
            import urllib.request
            req = urllib.request.Request(
                f"https://api.github.com/repos/{owner}/{repo}/pulls",
                data=json.dumps({"title": title, "body": body, "head": branch, "base": "main"}).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "ISHA-Senior-Dev",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return True, data.get("html_url", "")
        except Exception:
            pass

    # 3. Fallback: Direct 1-click GitHub PR URL
    if m:
        owner, repo = m.group(1), m.group(2)
        url = f"https://github.com/{owner}/{repo}/pull/new/{branch}"
        return True, f"Pushed! Open Pull Request in 1 click: {url}"

    return False, "Could not determine GitHub remote URL to open PR."

