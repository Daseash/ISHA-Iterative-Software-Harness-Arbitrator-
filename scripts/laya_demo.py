#!/usr/bin/env python3
"""
ISHA — LAYA-Judged Pipeline Demo

Standalone showcase of ISHA's full decision loop:
candidate patches → LAYA scoring → arbitration → danger check → verification.

Usage:
    python scripts/laya_demo.py           # demo mode (no API keys needed)
    python scripts/laya_demo.py --live    # live mode (uses .env keys when valid)
"""

import argparse
import sys
from pathlib import Path

# Windows consoles default to cp1252 which can't print Unicode characters
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DEMO_ISSUE = "subtract method in calculator.py returns a+b instead of a-b"
DEMO_PLAN = (
    "Step 1: root cause — subtract() returns a + b instead of a - b.\n"
    "Step 2: replace the return expression in subtract() with a - b."
)

CANDIDATES = [
    {
        "strategy": "minimal_diff",
        "file": "calculator.py",
        "patch": "--- a/calculator.py\n+++ b/calculator.py\n"
        "@@ -23,7 +23,7 @@ class Calculator:\n"
        "-        return a + b\n"
        "+        return a - b\n",
        "note": "correct fix",
    },
    {
        "strategy": "call_site_aware",
        "file": "calculator.py",
        "patch": "--- a/calculator.py\n+++ b/calculator.py\n"
        "@@ -23,7 +23,7 @@ class Calculator:\n"
        "-        return a + b\n"
        "+        return a * b\n",
        "note": "wrong operator",
    },
    {
        "strategy": "alt_test_phrasing",
        "file": "calculator.py",
        "patch": "--- a/calculator.py\n+++ b/calculator.py\n"
        "@@ -23,7 +23,7 @@ class Calculator:\n"
        "-        return a + b\n"
        "+        return eval(f'{a} - {b}')\n",
        "note": "dangerous shortcut",
    },
]

BAR_WIDTH = 14


def _bar(value: float, scale: float = 1.0) -> str:
    filled = int(round((value / scale) * BAR_WIDTH)) if scale else 0
    filled = max(0, min(BAR_WIDTH, filled))
    return "█" * filled + "░" * (BAR_WIDTH - filled)


def _line(label: str, value: float, scale: float = 1.0) -> str:
    pct = int(round((value / scale) * 100)) if scale else 0
    return f"      {label:<15} {value:>5.2f} / {scale:<4.1f}  {_bar(value, scale)} {pct:>3d}%"


def _live_candidates(issue: str) -> list:
    """Generate candidate patches with the configured LLMs (Gemini + Groq)."""
    from src.config import call_coder, call_planner

    plan = call_planner(
        "Produce a 2-step fix plan for this bug report. Output the plan only.\n\n"
        f"BUG REPORT:\n{issue}"
    )
    strategies = ["minimal_diff", "call_site_aware", "alt_test_phrasing"]
    hints = {
        "minimal_diff": "smallest possible diff",
        "call_site_aware": "consider every call site of the function",
        "alt_test_phrasing": "an alternative interpretation of the report",
    }
    out = []
    for strategy in strategies:
        patch = call_coder(
            f"Generate a unified diff patch to fix this bug ({hints[strategy]}). "
            f"Output ONLY the diff.\n\nBUG REPORT:\n{issue}\n\nPLAN:\n{plan}"
        )
        out.append({"strategy": strategy, "file": "target.py", "patch": patch, "note": "llm"})
    return out, plan


def run(issue: str, live: bool = False) -> int:
    print("=" * 50)
    print("  🤖 ISHA — LAYA-Judged Pipeline Demo")
    print("=" * 50)
    print(f'\nIssue: "{issue}"\n')

    plan = DEMO_PLAN
    candidates = CANDIDATES
    if live:
        from src.config import LLM_ENABLED

        if LLM_ENABLED:
            print("  mode: LIVE (Gemini/Groq generate the candidates)\n")
            candidates, plan = _live_candidates(issue)
        else:
            print("  mode: no API keys found — falling back to demo candidates\n")
    else:
        print("  mode: DEMO (hardcoded candidates, no keys required)\n")

    from src.review.laya_judge import get_judge

    judge = get_judge()

    scored = []
    for i, candidate in enumerate(candidates, start=1):
        scores = judge.score_patch(issue, plan, candidate["patch"])
        scored.append((scores["composite"], candidate, scores))
        print(f"📋 Candidate {i} ({candidate['strategy']} strategy):")
        print(f"   Patch: {_summarise(candidate['patch'])}")
        print("   LAYA Scores:")
        print(_line("fix_quality", scores["fix_quality"], 2.0))
        print(_line("matches_issue", scores["matches_issue"]))
        print(_line("safe_to_apply", scores["safe_to_apply"]))
        print(_line("composite", scores["composite"]))
        if scores["safe_to_apply"] < 0.3:
            print("      ⚠️  DANGER: unsafe patch")
        print()

    scored.sort(key=lambda row: row[0], reverse=True)
    composite, winner, _ = scored[0]

    dangers = judge.check_dangers(winner["patch"])
    verification = judge.verify_output(
        winner["patch"], issue
    )

    print(f"🏆 WINNER: {winner['strategy']} (composite: {composite:.3f})")
    status = "CLEAR ✅" if not dangers["flagged"] else f"FLAGGED ⚠️ {dangers}"
    print(f"🔍 Danger Check: {status}")
    verdict = "✅" if verification["passed"] else "❌"
    print(f"🔎 Final Verification: P(correct) = {verification['correct_probability']:.2f} {verdict}")
    print("=" * 50)
    return 0 if (verification["passed"] and not dangers["flagged"]) else 1


def _summarise(patch: str, limit: int = 70) -> str:
    changed = [ln for ln in patch.splitlines() if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---"))]
    text = " → ".join(changed[:2]) if changed else patch[:limit]
    return text[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description="ISHA LAYA pipeline demo")
    parser.add_argument("--live", action="store_true", help="Use Gemini/Groq for candidates")
    parser.add_argument("--issue", type=str, default=DEMO_ISSUE, help="Bug report to judge")
    args = parser.parse_args()
    return run(args.issue, live=args.live)


if __name__ == "__main__":
    raise SystemExit(main())
