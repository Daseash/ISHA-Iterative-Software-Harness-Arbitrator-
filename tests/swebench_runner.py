"""
ISHA SWE-bench Runner — benchmarks the agent on SWE-bench Lite.

Two modes:

  judge   (default)  LAYA scores the golden patch vs. a corrupted inverse
                     of it. Works offline and measures the discrimination
                     of the judgment component itself.
  full                Run the compiled graph against a local checkout of
                     each instance (--repo-root) and compare the generated
                     patch to the golden patch (file + line overlap).

Dataset loading uses HuggingFace `datasets` when installed, otherwise the
bundled fixture in tests/fixtures/swebench_lite_sample.jsonl (3 real
SWE-bench Lite instances).

Usage:
    python tests/swebench_runner.py --limit 3
    python tests/swebench_runner.py --mode full --repo-root /data/swe-bench --limit 10
"""

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURE = ROOT / "tests" / "fixtures" / "swebench_lite_sample.jsonl"
RESULTS = ROOT / "output" / "results.json"

# Rough token estimate for cost bookkeeping (USD per 1M prompt tokens).
_GEMINI_PRICE_PER_M = 0.30


# ── Dataset loading ────────────────────────────────────────────────────────
def load_tasks(dataset: str, limit: int) -> tuple:
    """Return (tasks, source_label) for the requested SWE-bench split."""
    try:
        from datasets import load_dataset  # pyrefly: ignore[missing-import]

        ds = load_dataset(dataset, split="test")
        rows = [ds[i] for i in range(min(limit, len(ds)))]
        tasks = [
            {
                "instance_id": r.get("instance_id", f"task-{i}"),
                "repo": r.get("repo", ""),
                "base_commit": r.get("base_commit", ""),
                "problem_statement": r.get("problem_statement", ""),
                "patch": r.get("patch", ""),
                "fail_to_pass": json.loads(r.get("FAIL_TO_PASS") or "[]")[:5],
            }
            for i, r in enumerate(rows)
        ]
        return tasks, f"huggingface:{dataset}"
    except Exception as exc:
        if not FIXTURE.exists():
            raise SystemExit(f"No dataset available and no fixture found: {exc}")
        tasks = [json.loads(line) for line in FIXTURE.read_text(encoding="utf-8").splitlines() if line.strip()]
        return tasks[:limit], f"bundled fixture ({type(exc).__name__}: {exc.__class__.__name__})"


# ── Patch comparison ───────────────────────────────────────────────────────
def _changed_lines(patch: str) -> set:
    return {
        line[1:].strip()
        for line in (patch or "").splitlines()
        if line[:1] in "+-" and not line.startswith(("+++", "---")) and line[1:].strip()
    }


def patch_overlap(generated: str, golden: str) -> dict:
    """Compare a generated patch against the golden patch."""
    gen, gold = _changed_lines(generated), _changed_lines(golden)
    union = gen | gold
    return {
        "identical": bool(generated) and generated.strip() == (golden or "").strip(),
        "golden_lines": len(gold),
        "generated_lines": len(gen),
        "line_overlap": (len(gen & gold) / len(union)) if union else 0.0,
        "covers_golden": bool(gold) and gold <= gen,
    }


def corrupt_patch(patch: str) -> str:
    """Invert a patch's hunks — an anti-fix used as the negative control."""
    flipped = []
    for line in (patch or "").splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            flipped.append("-" + line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            flipped.append("+" + line[1:])
        else:
            flipped.append(line)
    return "\n".join(flipped) + ("\n" if flipped else "")


UNRELATED_PATCH = (
    "--- a/README.rst\n+++ b/README.rst\n"
    "@@ -1,4 +1,4 @@\n-Old project title\n+Renamed project title\n"
)

DANGEROUS_PATCH = (
    "--- a/setup.py\n+++ b/setup.py\n"
    "@@ -1,4 +1,6 @@\n import os\n+eval(\"1+1\")\n+os.system(\"rm -rf /\")\n"
)


def _estimate_cost(task: dict) -> float:
    """Rough USD estimate for judging one task (0 when offline)."""
    from src.config import LLM_ENABLED

    if not LLM_ENABLED:
        return 0.0
    tokens = (len(task.get("problem_statement", "")) + len(task.get("patch", ""))) / 4
    return round(tokens / 1_000_000 * _GEMINI_PRICE_PER_M, 6)


# ── Modes ──────────────────────────────────────────────────────────────────
def run_judge(tasks: list) -> list:
    """Score the golden patch against three negative controls with LAYA."""
    from src.guardrails.scanner import scan_patch_for_secrets
    from src.review.laya_judge import get_judge

    judge = get_judge()
    results = []
    for task in tasks:
        started = time.time()
        issue = task["problem_statement"]
        golden = judge.score_patch(issue, "", task["patch"])
        inverted = judge.score_patch(issue, "", corrupt_patch(task["patch"]))
        unrelated = judge.score_patch(issue, "", UNRELATED_PATCH)

        dangers = judge.check_dangers(DANGEROUS_PATCH)
        clean, findings = scan_patch_for_secrets(DANGEROUS_PATCH)
        danger_flagged = bool(dangers["flagged"] or not clean)

        golden_danger = judge.check_dangers(task["patch"])["flagged"]
        results.append(
            {
                "instance_id": task["instance_id"],
                "repo": task["repo"],
                "mode": "judge",
                "golden_composite": round(golden["composite"], 4),
                "corrupt_composite": round(inverted["composite"], 4),
                "unrelated_composite": round(unrelated["composite"], 4),
                "danger_flagged": danger_flagged,
                "danger_findings": findings,
                "golden_approved": bool(golden["composite"] >= 0.5 and not golden_danger),
                "corrupt_rejected": bool(inverted["composite"] < golden["composite"]),
                "unrelated_rejected": bool(unrelated["composite"] < golden["composite"]),
                "latency_s": round(time.time() - started, 2),
                "cost_estimate_usd": _estimate_cost(task),
            }
        )
    return results


def run_full(tasks: list, repo_root: Path, thread_prefix: str = "swe") -> list:
    """Run the compiled graph against local checkouts and compare patches."""
    from src.agents.context import build_repo_context
    from src.agents.graph import compiled_graph
    from src.agents.state import AgentState

    results = []
    for index, task in enumerate(tasks, start=1):
        repo_dir = repo_root / task["instance_id"].replace("/", "__")
        started = time.time()
        record = {
            "instance_id": task["instance_id"],
            "repo": task["repo"],
            "mode": "full",
            "latency_s": 0.0,
            "cost_estimate_usd": _estimate_cost(task),
        }
        if not repo_dir.is_dir():
            record.update(
                {
                    "status": f"skipped — checkout not found at {repo_dir}",
                    "resolved": False,
                }
            )
            results.append(record)
            continue

        issue = task["problem_statement"]
        state = AgentState(
            issue_text=issue,
            repo_path=str(repo_dir),
            repo_context=build_repo_context(issue, str(repo_dir)),
        )
        out = compiled_graph.invoke(
            state,
            config={"configurable": {"thread_id": f"{thread_prefix}-{index}", "approval_mode": "auto"}},
        )
        result = AgentState(**out) if isinstance(out, dict) else out

        comparison = patch_overlap(result.patch, task["patch"])
        approved = result.critic_verdict in ("approved", "low_quality")
        record.update(
            {
                "status": "completed",
                "generated_patch": result.patch,
                "retries": result.retry_count,
                "verdict": result.critic_verdict,
                "laya_composite": round(result.critic_score, 4),
                "resolved": bool(approved and comparison["identical"]),
                **comparison,
                "latency_s": round(time.time() - started, 2),
            }
        )
        results.append(record)
    return results


# ── Reporting ──────────────────────────────────────────────────────────────
def print_summary(results: list, source: str, mode: str) -> dict:
    print("\n" + "=" * 78)
    print(f"  ISHA · SWE-bench Lite — mode={mode}  source={source}")
    print("=" * 78)

    if mode == "judge":
        print(
            f"  {'instance':<30} {'golden':>7} {'invert':>7} {'unrel':>7} "
            f"{'danger':>7} {'correct':>8} {'s':>6}"
        )
        print("  " + "-" * 74)
        for row in results:
            discrimination = (
                row["golden_approved"]
                and row["corrupt_rejected"]
                and row["unrelated_rejected"]
                and row["danger_flagged"]
            )
            print(
                f"  {row['instance_id']:<30} {row['golden_composite']:>7.3f} "
                f"{row['corrupt_composite']:>7.3f} {row['unrelated_composite']:>7.3f} "
                f"{'FLAG' if row['danger_flagged'] else 'miss':>7} "
                f"{'YES' if discrimination else 'no':>8} {row['latency_s']:>6.1f}"
            )
        n = max(len(results), 1)
        summary = {
            "mode": "judge",
            "source": source,
            "tasks": len(results),
            "golden_approval_rate": round(sum(r["golden_approved"] for r in results) / n, 3),
            "corrupt_rejection_rate": round(sum(r["corrupt_rejected"] for r in results) / n, 3),
            "unrelated_rejection_rate": round(sum(r["unrelated_rejected"] for r in results) / n, 3),
            "danger_detection_rate": round(sum(r["danger_flagged"] for r in results) / n, 3),
            "discrimination_rate": round(
                sum(
                    r["golden_approved"]
                    and r["corrupt_rejected"]
                    and r["unrelated_rejected"]
                    and r["danger_flagged"]
                    for r in results
                )
                / n,
                3,
            ),
            "avg_latency_s": round(sum(r["latency_s"] for r in results) / n, 2),
            "cost_estimate_usd": round(sum(r["cost_estimate_usd"] for r in results), 6),
        }
        print("  " + "-" * 74)
        print(
            f"  golden approved {summary['golden_approval_rate']:.0%} · "
            f"inverted rejected {summary['corrupt_rejection_rate']:.0%} · "
            f"unrelated rejected {summary['unrelated_rejection_rate']:.0%} · "
            f"danger flagged {summary['danger_detection_rate']:.0%} · "
            f"all four {summary['discrimination_rate']:.0%}"
        )
    else:
        print(f"  {'instance':<32} {'resolved':>9} {'overlap':>8} {'score':>7} {'s':>7}")
        print("  " + "-" * 74)
        for row in results:
            print(
                f"  {row['instance_id']:<32} {'yes' if row.get('resolved') else 'no':>9} "
                f"{row.get('line_overlap', 0.0):>8.2f} {row.get('laya_composite', 0.0):>7.3f} "
                f"{row['latency_s']:>7.1f}"
            )
        n = max(len(results), 1)
        completed = [r for r in results if r.get("status") == "completed"]
        summary = {
            "mode": "full",
            "source": source,
            "tasks": len(results),
            "completed": len(completed),
            "resolved": sum(bool(r.get("resolved")) for r in results),
            "resolution_rate": round(sum(bool(r.get("resolved")) for r in results) / n, 3),
            "avg_overlap": round(
                sum(r.get("line_overlap", 0.0) for r in results) / n, 3
            ),
            "avg_latency_s": round(sum(r["latency_s"] for r in results) / n, 2),
            "cost_estimate_usd": round(sum(r["cost_estimate_usd"] for r in results), 6),
        }
        print("  " + "-" * 74)
        print(
            f"  resolved {summary['resolved']}/{summary['tasks']} "
            f"({summary['resolution_rate']:.0%}) · mean golden-line overlap "
            f"{summary['avg_overlap']:.0%}"
        )
    print("=" * 78)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="ISHA SWE-bench Lite runner")
    parser.add_argument("--dataset", default="princeton-nlp/SWE-bench_Lite", help="HF dataset id")
    parser.add_argument("--limit", type=int, default=3, help="Number of tasks to run")
    parser.add_argument("--mode", choices=["judge", "full"], default="judge", help="Evaluation mode")
    parser.add_argument("--repo-root", type=str, default="", help="Directory of local checkouts (full mode)")
    parser.add_argument("--output", type=str, default=str(RESULTS), help="Where to write results.json")
    args = parser.parse_args()

    tasks, source = load_tasks(args.dataset, args.limit)
    print(f"Loaded {len(tasks)} tasks from {source}")

    if args.mode == "full":
        if not args.repo_root:
            print("  full mode needs --repo-root with per-instance checkouts; "
                  "no checkouts were given, recording skips.")
        results = run_full(tasks, Path(args.repo_root) if args.repo_root else Path("."))
    else:
        results = run_judge(tasks)

    summary = print_summary(results, source, args.mode)
    payload = {"summary": summary, "results": results}
    Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  exported → {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
