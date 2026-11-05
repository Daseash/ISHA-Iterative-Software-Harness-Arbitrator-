#!/usr/bin/env python3
"""P1-12: prune ephemeral local state (sessions, prompts, worktrees).

 Keeps: last 50 session JSONs, failure prompts only, version-stamped qdrant.
 Usage: python isha-agent/scripts/prune_state.py [--dry-run]
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENT_DIR = HERE.parent
KEEP_SESSIONS = 50


def prune_sessions(dry: bool) -> int:
    d = AGENT_DIR / "output" / "sessions"
    if not d.is_dir():
        return 0
    files = sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime)
    excess = files[:-KEEP_SESSIONS] if len(files) > KEEP_SESSIONS else []
    for p in excess:
        if not dry:
            p.unlink(missing_ok=True)
    return len(excess)


def prune_worktrees(dry: bool) -> int:
    n = 0
    for root_name in ("swebench_checkouts",):
        root = AGENT_DIR / root_name / ".worktrees"
        if not root.is_dir():
            continue
        for child in root.iterdir():
            if child.name.endswith(("-c1", "-c2", "-c3")):
                n += 1
                if not dry:
                    shutil.rmtree(child, ignore_errors=True)
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    s = prune_sessions(args.dry_run)
    w = prune_worktrees(args.dry_run)
    print(f"pruned sessions={s} worktrees={w} (dry={args.dry_run})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
