"""
ISHA Benchmark Reporting — raw per-instance JSON + tables generated from it.

Nothing in this module invents numbers: every figure is derived from
``results/<run_id>/*/meta.json`` and the official harness report, and every
table printed anywhere else in the project is generated from these files.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from src.bench.classify import CATEGORIES, build_breakdown

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "results"
PROGRESS_MD = RESULTS_DIR / "progress.md"


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

    payload = {
        "run_id": run_id,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_instances": total,
        "resolved": resolved,
        "resolve_rate": round(resolved / total, 4) if total else 0.0,
        "instances_with_patch": with_patch,
        "patch_rate": round(with_patch / total, 4) if total else 0.0,
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
    lines = [
        f"### {payload['run_id']}",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Instances | {payload['total_instances']} |",
        f"| **Resolved (official harness)** | **{payload['resolved']} / "
        f"{payload['total_instances']} ({payload['resolve_rate']:.1%})** |",
        f"| Produced a patch | {payload['instances_with_patch']} "
        f"({payload['patch_rate']:.1%}) |",
        "",
        "Failure breakdown:",
        "",
        "| Failure category | Count | Share of unresolved |",
        "|---|---|---|",
    ]
    unresolved = max(payload["total_instances"] - payload["resolved"], 1)
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
    lines = [
        "| Metric | Before | After | Δ |",
        "|---|---|---|---|",
        f"| Resolve rate | {before['resolve_rate']:.1%} | {after['resolve_rate']:.1%} "
        f"| {after['resolve_rate'] - before['resolve_rate']:+.1%} |",
        f"| Resolved | {before['resolved']}/{before['total_instances']} | "
        f"{after['resolved']}/{after['total_instances']} | "
        f"{after['resolved'] - before['resolved']:+d} |",
        f"| Patch rate | {before['patch_rate']:.1%} | {after['patch_rate']:.1%} "
        f"| {after['patch_rate'] - before['patch_rate']:+.1%} |",
        "",
        "| Failure category | Before | After |",
        "|---|---|---|",
    ]
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
