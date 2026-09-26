"""
ISHA — Autonomous AI Software Engineering Agent

Main CLI entry point. Accepts a bug report and runs the full agentic loop:
Plan → Regression Test → Patch → Sandbox → LAYA Judge

Usage:
    python src/main.py
    python src/main.py --issue "describe the bug here"
    python src/main.py --issue "..." --apply    # write the fix to the repo
"""

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import AGENT_NAME, LLM_ENABLED

DEFAULT_ISSUE = (
    "The subtract method in calculator.py returns a+b instead of a-b"
)


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


def _print_section(title: str, body: str, limit: int = 1200) -> None:
    body = (body or "").strip()
    if len(body) > limit:
        body = body[:limit] + "\n…[truncated]"
    print(f"\n── {title} " + "─" * max(4, 60 - len(title)))
    print(body if body else "(empty)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=f"{AGENT_NAME} — Autonomous AI Software Engineering Agent"
    )
    parser.add_argument("--issue", type=str, default=None, help="Bug report to fix")
    parser.add_argument(
        "--repo",
        type=str,
        default="tests/dummy_repo",
        help="Path to the target repository (default: tests/dummy_repo)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the validated patch into the real repo (default: sandbox only)",
    )
    parser.add_argument(
        "--thread-id", type=str, default="1", help="LangGraph checkpoint thread id"
    )
    parser.add_argument(
        "--multi",
        action="store_true",
        help="Run the multi-agent fan-out graph (3 strategies, 3 worktrees)",
    )
    args = parser.parse_args()

    issue = args.issue or DEFAULT_ISSUE
    using_default = args.issue is None

    print(BANNER)
    print(f"  Agent:  {AGENT_NAME}")
    print(f"  Models: {'Gemini Flash + Groq (live)' if LLM_ENABLED else 'offline deterministic brain (no API keys)'}")
    print(f"  Repo:   {args.repo}")
    print(f"  Issue:  {issue}")
    if using_default:
        print("  (no --issue given — running the built-in calculator demo bug)")

    from src.agents.context import build_repo_context
    from src.agents.graph import compiled_graph, compiled_multi_graph
    from src.agents.state import AgentState

    graph = compiled_multi_graph if args.multi else compiled_graph
    if args.multi:
        print("  Mode:  multi-agent (3 strategies in parallel worktrees)")

    state = AgentState(
        issue_text=issue,
        repo_path=args.repo,
        repo_context=build_repo_context(issue, args.repo),
    )

    print("\n  ▶ Running agentic loop: planner → regression test → coder → sandbox → critic")
    result = graph.invoke(
        state,
        config={
            "configurable": {"thread_id": args.thread_id, "apply": args.apply}
        },
    )
    if isinstance(result, dict):
        result = AgentState(**result)

    # Drain any branch attempts left in the arbitration ledger.
    from src.review.arbitration import collect_attempts

    collect_attempts(args.thread_id)

    _print_section("PLAN", result.plan)
    _print_section("REGRESSION TEST", result.regression_test, limit=800)
    _print_section("PATCH", result.patch, limit=2000)
    _print_section("TEST OUTPUT", result.test_output, limit=1500)
    _print_section(
        "LAYA SCORES",
        "\n".join(f"  {k}: {v}" for k, v in (result.laya_scores or {}).items()),
    )
    _print_section(
        "VERDICT",
        f"  critic_verdict: {result.critic_verdict}\n"
        f"  critic_score:   {result.critic_score:.3f}\n"
        f"  retries:        {result.retry_count}",
    )

    passed = "PASSED" in (result.test_output or "") and "FAILED" not in (
        result.test_output or ""
    )
    flagged = result.critic_verdict == "flagged"

    if args.apply and not args.multi and passed and not flagged and result.patch:
        from src.tools.patch_engine import apply_patch

        ok, message = apply_patch(args.repo, result.patch)
        print(f"\n  --apply: {'OK' if ok else 'FAILED'} — {message}")

    # Tidy up scratch sandboxes created during the run.
    import tempfile

    if result.worktree and Path(result.worktree).parent == Path(tempfile.gettempdir()):
        from src.tools.sandbox import cleanup_sandbox

        cleanup_sandbox(result.worktree)

    print()
    if passed and not flagged:
        print(f"  🤖 ISHA ✅ Fix applied "
              f"{'(in sandbox — pass --apply to write it)' if not args.apply else ''}")
        return 0
    if passed and flagged:
        print("  🤖 ISHA ⚠️ Tests pass but LAYA flagged the patch — human review required")
        return 2
    print(f"  🤖 ISHA ❌ Fix failed after {result.retry_count} retries")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
