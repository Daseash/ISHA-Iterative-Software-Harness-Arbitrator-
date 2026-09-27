#!/usr/bin/env python3
"""
ISHA — Live Demo

Runs the full autonomous fix pipeline end-to-end on the bundled
calculator bug and displays every stage with rich terminal formatting.

Works completely offline (no API keys needed) using the deterministic
offline brain + LAYA decision engine.

Usage:
    python scripts/demo.py                        # default subtract bug
    python scripts/demo.py --bug divide           # divide-by-zero bug
    python scripts/demo.py --bug subtract --multi # multi-agent mode
"""

import argparse
import io
import sys
import time
from pathlib import Path

# Windows consoles default to cp1252 which can't print Unicode box chars.
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BUGS = {
    "subtract": "The subtract method in calculator.py returns a+b instead of a-b",
    "divide": (
        "divide() in calculator.py doesn't handle division by zero — "
        "divide(10, 0) must raise ValueError('Cannot divide by zero') "
        "instead of ZeroDivisionError"
    ),
}

BANNER = """
+=====================================================================+
|                                                                       |
|   ISHA -- Autonomous AI Software Engineering Agent                    |
|                                                                       |
|   Plan -> Regression test (RED) -> Patch -> Sandbox -> Self-          |
|   correct loop -> LAYA verdict -> Approval gate -> Commit             |
|                                                                       |
|   Judgment:  LAYA calibrated probabilities (not heuristics)           |
|   Isolation: Git worktrees (multi-agent safe)                         |
|   Models:    Gemini 3.1 Flash Lite + Groq Qwen 3.8 (or offline)      |
|                                                                       |
+=====================================================================+
"""


def _sep(title: str = "", width: int = 70) -> None:
    if title:
        pad = width - len(title) - 4
        print(f"\n{'─' * 2} {title} {'─' * max(2, pad)}")
    else:
        print("─" * width)


def _step(emoji: str, label: str, detail: str = "") -> None:
    line = f"  {emoji}  {label}"
    if detail:
        line += f"  →  {detail}"
    print(line)


def _bar(value: float, scale: float = 1.0, width: int = 20) -> str:
    filled = int(round((value / scale) * width)) if scale else 0
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def _score_line(label: str, value: float, scale: float = 1.0) -> None:
    pct = int(round((value / scale) * 100)) if scale else 0
    bar = _bar(value, scale)
    print(f"     {label:<18} {value:>5.2f}/{scale:<4.1f}  {bar} {pct:>3d}%")


def run_demo(bug: str, multi: bool = False) -> int:
    issue = BUGS.get(bug)
    if not issue:
        print(f"Unknown bug: {bug}. Available: {', '.join(BUGS)}")
        return 1

    repo = str(ROOT / "tests" / "dummy_repo")
    if not Path(repo).is_dir():
        print(f"  🛑 Dummy repo not found: {repo}")
        return 1

    print(BANNER)

    # ── Show config ──────────────────────────────────────────────────
    from src.config import AGENT_NAME, LLM_ENABLED

    _sep("CONFIGURATION")
    _step("🔧", "Agent", AGENT_NAME)
    _step("🧠", "Models", "Gemini + Groq (live)" if LLM_ENABLED else "Offline deterministic brain")
    _step("📂", "Repo", repo)
    _step("🐛", "Bug", bug)
    _step("⚙️", "Mode", "Multi-agent (3 strategies)" if multi else "Single-agent")

    # ── Guardrail pre-check ──────────────────────────────────────────
    _sep("GUARDRAIL SCAN")
    from src.guardrails.scanner import scan_input_for_injection

    safe, reason = scan_input_for_injection(issue)
    if safe:
        _step("✅", "Input scan", "clean — no prompt injection detected")
    else:
        _step("🛑", "Input scan", f"BLOCKED — {reason}")
        return 3
    print(f"     Issue: \"{issue}\"")

    # ── Build context ────────────────────────────────────────────────
    _sep("BUILDING CONTEXT")
    from src.agents.context import build_repo_context

    t0 = time.time()
    context = build_repo_context(issue, repo)
    _step("🗺️", "AST map + RAG", f"built in {time.time() - t0:.1f}s ({len(context)} chars)")

    # ── Run the graph ────────────────────────────────────────────────
    _sep("RUNNING AGENTIC LOOP")
    from src.agents.graph import compiled_graph, compiled_multi_graph
    from src.agents.state import AgentState

    graph = compiled_multi_graph if multi else compiled_graph
    state = AgentState(issue_text=issue, repo_path=repo, repo_context=context)
    thread_id = f"demo-{int(time.time())}"

    t0 = time.time()
    _step("▶️", "Starting", "planner → regression test → coder → sandbox → critic")
    print()

    result = graph.invoke(
        state,
        config={
            "configurable": {
                "thread_id": thread_id,
                "apply": False,
                "approval_mode": "auto",
            }
        },
    )
    elapsed = time.time() - t0
    if isinstance(result, dict):
        result = AgentState(**result)

    # ── Drain arbitration leftovers ──────────────────────────────────
    from src.review.arbitration import collect_attempts

    collect_attempts(thread_id)

    # ── Display results ──────────────────────────────────────────────
    _sep("PLAN")
    plan = (result.plan or "(empty)").strip()
    for line in plan.splitlines()[:8]:
        print(f"     {line}")

    _sep("REGRESSION TEST")
    test = (result.regression_test or "(empty)").strip()
    for line in test.splitlines()[:12]:
        print(f"     {line}")
    if len(test.splitlines()) > 12:
        print(f"     ... ({len(test.splitlines()) - 12} more lines)")

    _sep("PATCH")
    patch = (result.patch or "(empty)").strip()
    for line in patch.splitlines()[:15]:
        prefix = "  "
        if line.startswith("+") and not line.startswith("+++"):
            prefix = "  +"
        elif line.startswith("-") and not line.startswith("---"):
            prefix = "  -"
        print(f"   {prefix} {line}")
    if len(patch.splitlines()) > 15:
        print(f"     ... ({len(patch.splitlines()) - 15} more lines)")

    _sep("TEST OUTPUT")
    output = (result.test_output or "(empty)").strip()
    # Show last 8 lines of test output (the summary)
    lines = output.splitlines()
    show = lines[-8:] if len(lines) > 8 else lines
    for line in show:
        print(f"     {line}")

    _sep("LAYA SCORES")
    scores = result.laya_scores or {}
    for key in ("fix_quality", "matches_issue", "safe_to_apply", "composite"):
        val = scores.get(key)
        if val is not None and isinstance(val, (int, float)):
            scale = 2.0 if key == "fix_quality" else 1.0
            _score_line(key, float(val), scale)
    for key in ("secrets_or_danger", "logic_drift"):
        val = scores.get(key)
        if val is not None and isinstance(val, (int, float)):
            flag = " ⚠️" if float(val) > 0.5 else ""
            _score_line(key, float(val), 1.0)
            if flag:
                print(f"     {'':18} {flag} FLAGGED")

    _sep("VERDICT")
    passed = "PASSED" in (result.test_output or "")
    flagged = result.critic_verdict == "flagged"
    print(f"     critic_verdict:  {result.critic_verdict}")
    print(f"     critic_score:    {result.critic_score:.3f}")
    print(f"     retries:         {result.retry_count}")
    print(f"     strategy:        {result.strategy}")
    print(f"     elapsed:         {elapsed:.1f}s")

    _sep("FINAL RESULT")
    if passed and not flagged:
        print("  🤖 ISHA ✅  Fix validated — tests pass, LAYA approved")
        print(f"     (sandbox only — pass --apply to write it to the repo)")
    elif passed and flagged:
        print("  🤖 ISHA ⚠️  Tests pass but LAYA flagged — human review required")
    else:
        print(f"  🤖 ISHA ❌  Fix failed after {result.retry_count} retries")
    print()

    return 0 if (passed and not flagged) else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ISHA Live Demo — runs the full autonomous fix pipeline"
    )
    parser.add_argument(
        "--bug",
        choices=list(BUGS),
        default="subtract",
        help="Which seeded bug to fix (default: subtract)",
    )
    parser.add_argument(
        "--multi",
        action="store_true",
        help="Run multi-agent mode (3 strategies in parallel worktrees)",
    )
    args = parser.parse_args()
    return run_demo(args.bug, multi=args.multi)


if __name__ == "__main__":
    raise SystemExit(main())
