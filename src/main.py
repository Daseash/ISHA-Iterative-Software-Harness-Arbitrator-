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
import logging
import os
import sys
import warnings
from pathlib import Path

# Suppress internal background worker and third-party library warnings
warnings.filterwarnings("ignore")
logging.getLogger("LiteLLM").setLevel(logging.CRITICAL)
logging.getLogger("litellm").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
os.environ["LITELLM_LOG"] = "CRITICAL"

# Windows consoles default to cp1252 which can't print Unicode box chars.
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import (
    AGENT_NAME,
    CODER_CHAIN,
    LLM_ENABLED,
    OFFLINE_MODE,
    PLANNER_CHAIN,
    TARGET_REPO_PATH,
    _short_name,
    get_model_log,
)

DEFAULT_ISSUE = (
    "The subtract method in calculator.py returns a+b instead of a-b"
)

# Phase 7 — subcommands live in src.cli; with no subcommand the historical
# single-issue behaviour below runs unchanged.
_CLI_COMMANDS = ("fix", "bench", "doctor", "report", "ui")


def _chain_line(label: str, chain: list) -> str:
    """Render one model chain: 'planner: gemini-3.5-flash (+2 fallbacks)'."""
    if OFFLINE_MODE:
        return f"|   {label:<8}: offline deterministic brain (no API keys)     |"
    primary = _short_name(chain[0])
    extra = len(chain) - 1
    suffix = f" (+{extra} fallback{'s' if extra != 1 else ''})" if extra else ""
    line = f"|   {label:<8}: {primary}{suffix}"
    return line.ljust(66)[:66] + "|"


def build_banner() -> str:
    """Banner rendered from the live model configuration in config.py."""
    return (
        "\n+===============================================================+\n"
        "|                                                                 |\n"
        "|   ISHA -- Autonomous AI Software Engineering Agent              |\n"
        "|                                                                 |\n"
        + _chain_line("planner", PLANNER_CHAIN) + "\n"
        + _chain_line("coder", CODER_CHAIN) + "\n"
        "|   Judgment:   LAYA calibrated probabilities (not heuristics)    |\n"
        "|   Isolation:  Git worktrees (multi-agent safe)                  |\n"
        "|                                                                 |\n"
        "+===============================================================+\n"
    )


BANNER = build_banner()


def _print_section(title: str, body: str, limit: int = 1200) -> None:
    body = (body or "").strip()
    if len(body) > limit:
        body = body[:limit] + "\n…[truncated]"
    print(f"\n── {title} " + "─" * max(4, 60 - len(title)))
    print(body if body else "(empty)")


def _format_model_usage(entries: list) -> str:
    """Render the model audit log: which model actually answered each step."""
    if not entries:
        return "(no model calls recorded)"
    lines = []
    for e in entries:
        line = f"  {e.get('role', '?'):<16} {e.get('model', '?'):<32} [{e.get('position', '?')}]"
        if e.get("note"):
            line += f" {e['note']}"
        lines.append(line)
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in _CLI_COMMANDS:
        from src.cli import main as cli_main

        return cli_main(sys.argv[1:])

    parser = argparse.ArgumentParser(
        description=f"{AGENT_NAME} — Autonomous AI Software Engineering Agent"
    )
    parser.add_argument("--issue", type=str, default=None, help="Bug report to fix")
    parser.add_argument(
        "--repo",
        type=str,
        default=TARGET_REPO_PATH,
        help="Path to the target repository to analyse and patch (default: TARGET_REPO_PATH env)",
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
    parser.add_argument(
        "--approve",
        choices=["auto", "cli"],
        default="auto",
        help="Approval gate mode: auto records it silently, cli prompts for y/N",
    )
    args = parser.parse_args()

    if not Path(args.repo).is_dir():
        print(build_banner())
        print(f"  🛑 Target repo not found: {args.repo}")
        print("     The bundled fixture was removed — pass --repo <path> to any")
        print("     Python repo you want ISHA to work on.")
        return 4

    issue = args.issue or DEFAULT_ISSUE
    using_default = args.issue is None

    from src.guardrails.scanner import scan_input_for_injection

    safe, reason = scan_input_for_injection(issue)
    if not safe:
        print(build_banner())
        print(f"  🛑 Blocked by guardrails: {reason}")
        return 3

    print(build_banner())
    print(f"  Agent:  {AGENT_NAME}")
    if LLM_ENABLED and not OFFLINE_MODE:
        print(f"  Planner chain: {' -> '.join(_short_name(m) for m in PLANNER_CHAIN)}")
        print(f"  Coder chain:   {' -> '.join(_short_name(m) for m in CODER_CHAIN)}")
    else:
        print("  Models: offline deterministic brain (no API keys)")
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
            "configurable": {
                "thread_id": args.thread_id,
                "apply": args.apply,
                "approval_mode": args.approve,
            }
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
    _print_section("MODEL USAGE", _format_model_usage(result.model_log or get_model_log()))

    from src.review.pr_formatter import format_draft_pr, save_run_history
    pr_doc = format_draft_pr(result, candidate=getattr(result, "selected_candidate", None))
    run_dir = save_run_history(result, pr_doc)
    _print_section("SENIOR-DEV DRAFT PR", pr_doc, limit=3000)
    print(f"\n  💾 Run history saved to: {run_dir}")

    passed = "PASSED" in (result.test_output or "") and "FAILED" not in (
        result.test_output or ""
    )
    flagged = result.critic_verdict == "flagged"

    if args.apply and not args.multi and passed and result.patch and (not flagged or result.approved is True):
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
        if result.approved is True:
            print("  🤖 ISHA ✅ Flagged patch approved by a human — fix applied")
            return 0
        print("  🤖 ISHA ⚠️ Tests pass but LAYA flagged the patch — human review required")
        return 2
    print(f"  🤖 ISHA ❌ Fix failed after {result.retry_count} retries")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
