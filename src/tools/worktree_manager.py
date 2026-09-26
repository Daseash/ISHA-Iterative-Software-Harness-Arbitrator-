"""
ISHA Worktree Manager — Isolated git worktrees for multi-agent attempts.

Each parallel agent gets its own working directory and branch so agents
never touch each other's files. Implemented in Phase 6.
"""


def create_worktree(repo_path: str, name: str) -> str:
    """Create an isolated git worktree for an agent attempt."""
    # TODO: Implement in Phase 6
    return ""


def remove_worktree(worktree_path: str) -> bool:
    """Remove a worktree and its branch after arbitration."""
    # TODO: Implement in Phase 6
    return False


def cleanup_all_worktrees(repo_path: str) -> None:
    """Remove all worktrees created by ISHA."""
    # TODO: Implement in Phase 6
    pass
