"""
ISHA — Autonomous AI Software Engineering Agent

Main CLI entry point. Accepts a bug report and runs the full agentic loop:
Plan → Patch → Test → LAYA Judge → Commit

Usage:
    python src/main.py
    python src/main.py --issue "describe the bug here"
"""

import argparse
import sys

from src.config import AGENT_NAME


BANNER = r"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🤖 ISHA — Autonomous AI Software Engineering Agent          ║
║                                                               ║
║   Powered by: Gemini Flash + Groq Llama 3.3 + LAYA Engine    ║
║   Judgment:   LAYA calibrated probabilities (not heuristics)  ║
║   Isolation:  Git worktrees (multi-agent safe)                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""


def main():
    parser = argparse.ArgumentParser(
        description=f"{AGENT_NAME} — Autonomous AI Software Engineering Agent"
    )
    parser.add_argument(
        "--issue",
        type=str,
        default=None,
        help="Bug report or issue description to fix",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default="tests/dummy_repo",
        help="Path to the target repository (default: tests/dummy_repo)",
    )

    args = parser.parse_args()

    print(BANNER)
    print(f"  Agent: {AGENT_NAME}")
    print(f"  Repo:  {args.repo}")
    print(f"  Phase: 1 — Skeleton (nodes implemented in later phases)")
    print()

    if args.issue:
        print(f"  📋 Issue: {args.issue}")
        print()
        print("  ⏳ Full pipeline available after Phase 5.")
        print("  Run `python src/main.py --issue 'your bug'` to test.")
    else:
        print("  💡 No issue provided. Use --issue to submit a bug report.")
        print("  Example: python src/main.py --issue 'subtract returns wrong result'")

    print()
    print(f"  🤖 {AGENT_NAME} is ready.\n")


if __name__ == "__main__":
    main()
