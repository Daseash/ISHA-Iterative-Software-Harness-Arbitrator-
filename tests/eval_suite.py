"""
ISHA Eval Suite — runs the platform against bundled target-repo bug fixtures.

The calculator fixture (tests/dummy_repo) was retired from the tree; the suite
now exits with a clear message unless REPO points at an existing repository.

For every case the single-agent graph runs end-to-end, then the generated
patch is applied to a pristine copy of the repository and pytest decides
whether the target test class actually goes green (resolution = FAIL_TO_PASS).

Usage:
    python tests/eval_suite.py
"""

import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPO = ROOT / "tests" / "dummy_repo"
OUTPUT = ROOT / "output" / "eval_results.json"

CASES = [
    {
        "id": "subtract_wrong_operator",
        "selector": "TestSubtract",
        "issue": "The subtract method in calculator.py returns a+b instead of a-b",
    },
    {
        "id": "divide_missing_zero_guard",
        "selector": "TestDivide",
        "issue": (
            "divide() in calculator.py doesn't handle division by zero — "
            "divide(10, 0) must raise ValueError('Cannot divide by zero') "
            "instead of ZeroDivisionError"
        ),
    },
    {
        "id": "subtract_rephrased_report",
        "selector": "TestSubtract",
        "issue": (
            "Unit test failure: TestSubtract::test_subtract_positive expects "
            "calc.subtract(5, 3) == 2 but gets 8. Looks like calculator.py "
            "subtracts the wrong way around."
        ),
    },
]


def verify_patch(patch: str, selector: str) -> dict:
    """Apply the patch to a pristine copy and check the target test class."""
    from src.tools.sandbox import cleanup_sandbox, run_in_sandbox

    if not (patch or "").strip():
        return {"applied": False, "resolved": False, "detail": "no patch produced"}

    sandbox, output = run_in_sandbox(str(REPO), patch)
    try:
        if output.startswith("FAILED: patch"):
            return {"applied": False, "resolved": False, "detail": output}
        failures = [
            line
            for line in output.splitlines()
            if line.startswith("FAILED") and "::" in line
        ]
        target_failures = [line for line in failures if f"::{selector}::" in line]
        summary_line = next(
            (line for line in reversed(output.splitlines()) if "passed" in line or "failed" in line),
            "",
        )
        return {
            "applied": True,
            "resolved": not target_failures,
            "failed_tests": failures,
            "summary": summary_line.strip(),
        }
    finally:
        cleanup_sandbox(sandbox)


def run_case(case: dict, index: int) -> dict:
    from src.agents.context import build_repo_context
    from src.agents.graph import compiled_graph
    from src.agents.state import AgentState

    issue = case["issue"]
    state = AgentState(
        issue_text=issue,
        repo_path=str(REPO),
        repo_context=build_repo_context(issue, str(REPO)),
    )

    started = time.time()
    out = compiled_graph.invoke(
        state,
        config={"configurable": {"thread_id": f"eval-{index}", "approval_mode": "auto"}},
    )
    latency = time.time() - started
    result = AgentState(**out) if isinstance(out, dict) else out

    check = verify_patch(result.patch, case["selector"])
    # Resolution requires the target class to go green AND LAYA to clear it.
    resolved = bool(check["resolved"] and result.critic_verdict in ("approved", "low_quality"))
    return {
        "id": case["id"],
        "selector": case["selector"],
        "issue": issue,
        "resolved": resolved,
        "tests_green": bool(check["resolved"]),
        "applied": bool(check.get("applied")),
        "verdict": result.critic_verdict,
        "laya_composite": round(result.critic_score, 4),
        "retries": result.retry_count,
        "latency_s": round(latency, 2),
        "failed_tests": check.get("failed_tests", []),
    }


def run_eval() -> int:
    print("=" * 78)
    print("  ISHA · Eval Suite — target-repo bug fixtures")
    print("=" * 78)

    if not REPO.is_dir():
        print(f"\n  🛑 Target fixture not found: {REPO}")
        print("     The bundled calculator fixture was removed, so these")
        print("     calculator-specific cases (TestSubtract / TestDivide) cannot run.")
        print("     Restore tests/dummy_repo, or edit CASES/REPO for your own repo.")
        return 2

    rows = []
    for index, case in enumerate(CASES, start=1):
        print(f"\n[{index}/{len(CASES)}] {case['id']}  ({case['selector']})")
        row = run_case(case, index)
        rows.append(row)
        mark = "✅" if row["resolved"] else ("🟡" if row["tests_green"] else "❌")
        print(
            f"    {mark} resolved={row['resolved']}  verdict={row['verdict']}  "
            f"composite={row['laya_composite']:.3f}  retries={row['retries']}  "
            f"{row['latency_s']:.1f}s"
        )
        if row["failed_tests"]:
            for failure in row["failed_tests"]:
                print(f"      failing: {failure}")

    count = max(len(rows), 1)
    resolved = sum(row["resolved"] for row in rows)
    summary = {
        "cases": len(rows),
        "resolved": resolved,
        "resolution_rate": round(resolved / count, 3),
        "avg_retries": round(sum(row["retries"] for row in rows) / count, 2),
        "avg_laya_composite": round(sum(row["laya_composite"] for row in rows) / count, 3),
        "avg_latency_s": round(sum(row["latency_s"] for row in rows) / count, 1),
    }

    print("\n" + "=" * 78)
    print(f"  {'case':<30} {'resolved':>9} {'verdict':>10} {'score':>7} {'ret':>4} {'s':>6}")
    print("  " + "-" * 74)
    for row in rows:
        print(
            f"  {row['id']:<30} {'yes' if row['resolved'] else 'no':>9} "
            f"{str(row['verdict']):>10} {row['laya_composite']:>7.3f} "
            f"{row['retries']:>4} {row['latency_s']:>6.1f}"
        )
    print("  " + "-" * 74)
    print(
        f"  resolved {summary['resolved']}/{summary['cases']} "
        f"({summary['resolution_rate']:.0%}) · avg retries {summary['avg_retries']} · "
        f"avg composite {summary['avg_laya_composite']:.3f} · "
        f"avg latency {summary['avg_latency_s']}s"
    )
    print("=" * 78)

    OUTPUT.write_text(json.dumps({"summary": summary, "cases": rows}, indent=2), encoding="utf-8")
    print(f"  exported → {OUTPUT}")
    return 0 if summary["resolved"] >= 1 else 1


if __name__ == "__main__":
    raise SystemExit(run_eval())
