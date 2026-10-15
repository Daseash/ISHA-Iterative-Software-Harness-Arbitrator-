#!/usr/bin/env python3
"""P2-07: cost/latency Pareto — per-model/strategy yield from results.

Free-tier $0, so Pareto is on yield-per-call and latency. Feeds the
quota-aware router (cheapest model clearing per-org threshold first).
Usage: python isha-agent/scripts/cost_report.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENT_DIR = HERE.parent
RESULTS_DIR = AGENT_DIR / "results"


def main() -> int:
    stats: dict = defaultdict(lambda: {"calls": 0, "patches": 0, "wins": 0, "elapsed": 0.0})
    for cand_file in [RESULTS_DIR / "candidates.json"]:
        if not cand_file.is_file():
            continue
        try:
            rows = json.loads(cand_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        for r in rows:
            key = (r.get("model_used", "?"), r.get("strategy", "?"))
            s = stats[key]
            s["calls"] += 1
            s["patches"] += 1 if r.get("patch_applied") else 0
            s["wins"] += 1 if r.get("won_selection") else 0
    print(f"{'model':<40} {'strategy':<18} {'calls':>6} {'applied%':>8} {'win%':>6}")
    for (model, strat), s in sorted(stats.items(), key=lambda kv: (-kv[1]["wins"], kv[0][0])):
        ap = s["patches"] / s["calls"] * 100 if s["calls"] else 0
        wp = s["wins"] / s["calls"] * 100 if s["calls"] else 0
        print(f"{model:<40} {strat:<18} {s['calls']:>6} {ap:>7.1f}% {wp:>5.1f}%")
    if not stats:
        print("(no candidates.json rows yet)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
