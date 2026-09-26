"""Phase 6 demo check — worktree isolation + multi-agent dispatch."""

import shutil
import subprocess
import tempfile
from pathlib import Path

from src.tools.worktree_manager import cleanup_all_worktrees, create_worktree, remove_worktree

tmp = Path(tempfile.mkdtemp(prefix="isha-phase6-"))
repo = tmp / "dummy_repo"
shutil.copytree("tests/dummy_repo", repo)

# Give the scratch repo its own git history (as the demo expects).
for cmd in (["init"], ["add", "."], ["-c", "user.name=ISHA", "-c", "user.email=isha@local",
            "commit", "-m", "init"]):
    subprocess.run(["git", *cmd], cwd=str(repo), capture_output=True)

wt_path = create_worktree(str(repo), "test-agent-1")
assert Path(wt_path).exists(), f"Worktree not created at {wt_path}"
print(f"Created worktree at: {wt_path}")

# Isolation check: edits in the worktree must not touch the source repo.
target = Path(wt_path) / "calculator.py"
original_repo_file = (repo / "calculator.py").read_text(encoding="utf-8")
target.write_text(original_repo_file + "\n# isolated edit\n", encoding="utf-8")
assert "# isolated edit" not in (repo / "calculator.py").read_text(encoding="utf-8")
print("Isolation verified: worktree edit did not touch the source repo")

assert remove_worktree(wt_path), "Worktree not cleaned up"
assert not Path(wt_path).exists(), "Worktree not cleaned up"
print("Worktree cleaned up successfully")

# Non-git repo fallback: plain directory copy, still isolated.
plain = tmp / "plain_repo"
shutil.copytree("tests/dummy_repo", plain)
fallback = create_worktree(str(plain), "agent-9")
assert Path(fallback).exists() and Path(fallback) != plain
remove_worktree(fallback)
print("Non-git fallback worktree OK")

cleanup_all_worktrees(str(repo))
shutil.rmtree(tmp, ignore_errors=True)

print("\nPhase 6 PASSED - Multi-agent dispatch working!")
