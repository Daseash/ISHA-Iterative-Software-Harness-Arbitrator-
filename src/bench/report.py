"""
ISHA Benchmark Reporting — raw per-instance JSON + tables generated from it.

Nothing in this module invents numbers: every figure is derived from
``results/<run_id>/*/meta.json`` and the official harness report, and every
table printed anywhere else in the project is generated from these files.
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    _reconf = getattr(_stream, "reconfigure", None)
    if callable(_reconf):
        try:
            _reconf(encoding="utf-8")
        except Exception:
            pass
from src.bench.classify import CATEGORIES, STAGE_NAMES, build_breakdown

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "results"
PROGRESS_MD = RESULTS_DIR / "progress.md"


def wilson_interval(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Calculate the Wilson score confidence interval for a binomial proportion."""
    if n <= 0:
        return (0.0, 0.0)
    z = 1.95996
    p_hat = k / n
    denom = 1.0 + (z ** 2) / n
    center = (p_hat + (z ** 2) / (2 * n)) / denom
    spread = (z / denom) * math.sqrt((p_hat * (1.0 - p_hat) / n) + ((z ** 2) / (4 * (n ** 2))))
    return (round(max(0.0, center - spread), 4), round(min(1.0, center + spread), 4))


def format_rate_ci(k: int, n: int) -> str:
    """Format count, percentage rate, and 95% Wilson confidence interval."""
    if n <= 0:
        return "0.0% [95% CI: 0.0% - 0.0%]"
    rate = k / n
    low, high = wilson_interval(k, n)
    return f"{rate:.1%} [95% CI: {low:.1%} - {high:.1%}]"


def load_run(run_id: str, records: list[dict] | None = None,
             report: dict | None = None) -> dict:
    """Build the raw result payload for one run."""
    run_dir = RESULTS_DIR / run_id
    if records is None:
        from src.bench import dataset as ds

        ids = ds.read_slice(run_id)
        all_records = ds.load_records()
        by_id = {r["instance_id"]: r for r in all_records}
        records = [by_id[i] for i in ids] if ids else []

    if report is None:
        from src.bench.harness_eval import load_official_report

        report = load_official_report(run_dir) or {}

    breakdown = build_breakdown(run_dir, records, report)
    total = len(records)
    resolved = sum(1 for row in breakdown["rows"] if row["resolved"])
    with_patch = sum(1 for row in breakdown["rows"] if row["has_patch"])

    stage_counts = breakdown.get("stage_counts", {})
    stage_breakdown = {}
    for s_name in STAGE_NAMES:
        c = stage_counts.get(s_name, 0)
        low, high = wilson_interval(c, total)
        stage_breakdown[s_name] = {
            "count": c,
            "rate": round(c / total, 4) if total else 0.0,
            "ci_95": [low, high],
        }

    res_ci = wilson_interval(resolved, total)
    patch_ci = wilson_interval(with_patch, total)

    payload = {
        "run_id": run_id,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_instances": total,
        "resolved": resolved,
        "resolve_rate": round(resolved / total, 4) if total else 0.0,
        "resolve_ci_95": list(res_ci),
        "instances_with_patch": with_patch,
        "patch_rate": round(with_patch / total, 4) if total else 0.0,
        "patch_ci_95": list(patch_ci),
        "stage_breakdown": stage_breakdown,
        "failure_breakdown": {k: breakdown["counts"].get(k, 0) for k in CATEGORIES},
        "official_report": {
            k: report.get(k)
            for k in (
                "total_instances",
                "submitted_instances",
                "completed_instances",
                "resolved_instances",
                "unresolved_instances",
                "empty_patch_instances",
                "error_instances",
                "infra_failure_instances",
                "ambiguous_failure_instances",
            )
            if k in report
        },
        "instances": breakdown["rows"],
    }
    return payload


def write_run_json(payload: dict) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{payload['run_id']}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def render_table(payload: dict) -> str:
    total = payload["total_instances"]
    resolved = payload["resolved"]
    with_patch = payload["instances_with_patch"]
    lines = [
        f"### {payload['run_id']}",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Instances (sample size) | {total} |",
        f"| **Resolved (official harness)** | **{resolved} / {total} ({format_rate_ci(resolved, total)})** |",
        f"| Produced a patch | {with_patch} / {total} ({format_rate_ci(with_patch, total)}) |",
        "",
        "Stage breakdown:",
        "",
        "| Stage outcome | Count / Total | Rate (95% Wilson CI) |",
        "|---|---|---|",
    ]
    sb = payload.get("stage_breakdown") or {}
    for s_name in STAGE_NAMES:
        item = sb.get(s_name, {})
        c = item.get("count", 0)
        lines.append(f"| `{s_name}` | {c} / {total} | {format_rate_ci(c, total)} |")
    lines.append("")
    lines.append("Failure breakdown:")
    lines.append("")
    lines.append("| Failure category | Count | Share of unresolved |")
    lines.append("|---|---|---|")
    unresolved = max(total - resolved, 1)
    for category in CATEGORIES:
        count = payload["failure_breakdown"].get(category, 0)
        lines.append(f"| `{category}` | {count} | {count / unresolved:.1%} |")
    lines.append("")
    return "\n".join(lines)


def append_progress(section_title: str, body: str) -> Path:
    """Append a dated before/after block to results/progress.md."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if not PROGRESS_MD.is_file():
        PROGRESS_MD.write_text(
            "# ISHA SWE-bench progress log\n\n"
            "Every block below was produced from `results/*.json` and the "
            "official harness report. No number here is estimated.\n",
            encoding="utf-8",
        )
    with PROGRESS_MD.open("a", encoding="utf-8") as fh:
        fh.write(f"\n## {section_title} — {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        fh.write(body.rstrip() + "\n")
    return PROGRESS_MD


def compare(before: dict, after: dict) -> str:
    """Render a before/after table for two run payloads."""
    b_tot = before["total_instances"]
    a_tot = after["total_instances"]
    b_res = before["resolved"]
    a_res = after["resolved"]
    b_pat = before["instances_with_patch"]
    a_pat = after["instances_with_patch"]
    lines = [
        "| Metric | Before | After | Δ |",
        "|---|---|---|---|",
        f"| Resolve rate | {format_rate_ci(b_res, b_tot)} | {format_rate_ci(a_res, a_tot)} "
        f"| {after['resolve_rate'] - before['resolve_rate']:+.1%} |",
        f"| Resolved | {b_res}/{b_tot} | {a_res}/{a_tot} | {a_res - b_res:+d} |",
        f"| Patch rate | {format_rate_ci(b_pat, b_tot)} | {format_rate_ci(a_pat, a_tot)} "
        f"| {after['patch_rate'] - before['patch_rate']:+.1%} |",
        "",
        "Stage breakdown comparison:",
        "",
        "| Stage outcome | Before | After | Δ |",
        "|---|---|---|---|",
    ]
    b_sb = before.get("stage_breakdown") or {}
    a_sb = after.get("stage_breakdown") or {}
    for s_name in STAGE_NAMES:
        b_c = b_sb.get(s_name, {}).get("count", 0)
        a_c = a_sb.get(s_name, {}).get("count", 0)
        b_rate = b_c / b_tot if b_tot else 0.0
        a_rate = a_c / a_tot if a_tot else 0.0
        lines.append(f"| `{s_name}` | {format_rate_ci(b_c, b_tot)} | {format_rate_ci(a_c, a_tot)} | {a_rate - b_rate:+.1%} |")
    lines.append("")
    lines.append("| Failure category | Before | After |")
    lines.append("|---|---|---|")
    for category in CATEGORIES:
        b = before["failure_breakdown"].get(category, 0)
        a = after["failure_breakdown"].get(category, 0)
        marker = "" if a <= b else " ⚠️"
        lines.append(f"| `{category}` | {b} | {a}{marker} |")
    return "\n".join(lines)


def summarize(run_id: str) -> dict:
    payload = load_run(run_id)
    write_run_json(payload)
    return payload


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Aggregate a benchmark run")
    parser.add_argument("run_id", nargs="?", default="")
    parser.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"))
    args = parser.parse_args()

    if args.compare:
        before, after = (summarize(r) for r in args.compare)
        print(compare(before, after))
        return 0
    if not args.run_id:
        print("Available runs:")
        for path in sorted(RESULTS_DIR.glob("*.json")):
            print(" ", path.stem)
        return 0
    payload = summarize(args.run_id)
    print(render_table(payload))
    print(f"wrote {RESULTS_DIR / (args.run_id + '.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
