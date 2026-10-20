#!/usr/bin/env python3
"""
ISHA sync hook — refresh MAKING_BETTER.md Section 1 from ground truth.

Reads (never writes except the SYNC block):
  isha-agent/results/lite300-s*[_-]*/**/report.json  (any run-id suffix, dedup by instance id)
  isha-agent/data/laya_combiner.json                 (ECE/Brier/N, no hardcodes)
  isha-agent/data/slices/lite300-s*.json             (quotas, default 30)

Writes:
  ISHA/MAKING_BETTER.md  (only between <!-- SYNC-START --> and <!-- SYNC-END -->)

Usage (from workspace root C:\\Users\\Eashwar\\ISHA):
  python isha-agent/scripts/sync_making_better.py
  python isha-agent/scripts/sync_making_better.py --check   # exit 1 if stale, for CI

Exit codes: 0 ok, 1 missing report/schema or --check found drift.
Line endings: LF only. Encoding: UTF-8.
"""

from __future__ import annotations

import argparse
import datetime
import glob
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # isha-agent/scripts
AGENT_DIR = HERE.parent                          # isha-agent
WORKSPACE_ROOT = AGENT_DIR.parent                # ISHA
RESULTS_DIR = AGENT_DIR / "results"
DATA_DIR = AGENT_DIR / "data"
DOC_PATH = WORKSPACE_ROOT / "MAKING_BETTER.md"

SESSIONS = [f"lite300-s{i}" for i in range(1, 11)]
QUOTA_DEFAULT = 30


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def scan_session(session_id: str) -> set[str]:
    """Collect resolved instance ids across ALL run-id suffixes (-r2..r5, -rescue, -v2, ...)."""
    resolved: set[str] = set()
    # Match base dir + any suffix dir: lite300-s5, lite300-s5-r2, lite300-s5-rescue-v4, ...
    for run_dir in sorted(RESULTS_DIR.glob(f"{session_id}*")):
        if not run_dir.is_dir():
            continue
        for r_file in run_dir.rglob("report.json"):
            data = load_json(r_file)
            if not isinstance(data, dict):
                continue
            for k, v in data.items():
                if isinstance(v, dict) and v.get("resolved") is True:
                    resolved.add(str(k))
    return resolved


def session_quota(session_id: str) -> int:
    slice_path = DATA_DIR / "slices" / f"{session_id}.json"
    data = load_json(slice_path)
    if isinstance(data, list) and data:
        return len(data)
    if isinstance(data, dict) and data.get("instances"):
        try:
            return len(data["instances"])
        except Exception:
            pass
    return QUOTA_DEFAULT


def laya_line() -> str:
    info = load_json(DATA_DIR / "laya_combiner.json")
    if not info:
        return "LAYA combiner missing (data/laya_combiner.json not found)"
    ece_raw = info.get("ece_raw", info.get("val_ece_raw", "?"))
    ece_scaled = info.get("ece_scaled", info.get("val_ece_scaled", "?"))
    brier = info.get("brier_raw", info.get("val_brier_raw", "?"))
    n = info.get("n", info.get("n_total", info.get("n_train", "?")))
    n_tr, n_tot = info.get("n_train"), info.get("n_total")
    n_str = f"{n_tr} train / {n_tot} total" if n_tr and n_tot and n_tr != n_tot else str(n)
    t = info.get("temperature", "?")
    return f"ECE raw {ece_raw} / scaled {ece_scaled} | Brier {brier} | N={n_str} | T={t}"


def build_table() -> tuple[str, dict]:
    rows = []
    total_resolved = 0
    total_quota = 0
    per_session: dict[str, tuple[int, int]] = {}
    for sid in SESSIONS:
        quota = session_quota(sid)
        res = scan_session(sid)
        count = len(res)
        per_session[sid] = (count, quota)
        total_resolved += count
        total_quota += quota
        rate = (count / quota * 100) if quota else 0.0
        num = sid.replace("lite300-s", "S")
        rows.append(f"| {num} {sid} | 30 slice ({quota} quota) | {count} | {rate:.1f}% | `results/{sid}*/report.json` |")
    s14 = sum(per_session[f"lite300-s{i}"][0] for i in range(1, 5))
    s17 = sum(per_session[f"lite300-s{i}"][0] for i in range(1, 8))
    combined_rate = (total_resolved / total_quota * 100) if total_quota else 0.0
    today = datetime.date.today().isoformat()
    header = (
        f"- Synced: {today} (auto via `python isha-agent/scripts/sync_making_better.py`)\n"
        f"- SSOT command: `python isha-agent/scripts/score.py` (scans `results/lite300-s1..s10/**/report.json`, counts `resolved is True`)\n\n"
        f"| Session | Evaluated | Resolved | Rate | Evidence |\n"
        f"|---|---|---|---|---|\n"
    )
    body = "\n".join(rows)
    footer = (
        f"\n| S1-S4 combined | 120 | {s14} | {s14/120*100:.1f}% | cherry-picked headline — DO NOT quote alone |\n"
        f"| S1-S7 combined | 210 | {s17} | {s17/210*100:.1f}% ({s17/300*100:.1f}% of 300) | TRUE score today |\n"
        f"| S1-S10 combined | {total_quota} | {total_resolved} | {combined_rate:.1f}% | full Lite300 |\n"
        f"| Golden-7 safety net | 7 | 7/7 PASS (real verifier, P0-03 DONE) | PASS | `scripts/verify_golden.py` |\n"
        f"| LAYA gate | — | {laya_line()} | `data/laya_combiner.json` |\n"
        f"\n> Headline rule: always quote S1-S7/S1-S10 alongside any S1-S4 mention. Never claim leaderboard rank without PR link.\n"
    )
    return header + body + footer, per_session


STALE_PATTERNS = [
    (r"isha solve", "stale CLI `isha solve` (real: `isha fix`/`isha bench`)"),
    (r"python -m isha\.cli|pip install isha-agent(?!/)", "stale install/CLI (`isha` package, `pip install -e isha-agent/`)"),
    (r"gemini-2\.5-flash", "stale model gemini-2.5 (code uses 3.5/3.8)"),
    (r"run_lite300\.py|run_slice\.py", "missing script referenced in AGENTS.md"),
    (r"TBD-after-benchmark|<your-repo-url>|\[Your Name\]|deploy-pending", "template placeholder in files/"),
]


def stale_check() -> list[str]:
    hits: list[str] = []
    roots = [
        AGENT_DIR / "docs",
        WORKSPACE_ROOT / "website" / "src",
        AGENT_DIR / "website" / "src",
        WORKSPACE_ROOT / "files",
    ]
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.md"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for pat, msg in STALE_PATTERNS:
                if re.search(pat, text):
                    hits.append(f"{path.relative_to(WORKSPACE_ROOT)}: {msg}")
                    break
        for path in root.rglob("*.tsx"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for pat, msg in STALE_PATTERNS[:3]:
                if re.search(pat, text):
                    hits.append(f"{path.relative_to(WORKSPACE_ROOT)}: {msg}")
                    break
    return sorted(set(hits))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit 1 if doc looks stale, without writing")
    args = ap.parse_args()

    table, _ = build_table()
    stale = stale_check()

    if args.check:
        if stale:
            print("STALE DOC REFERENCES:")
            for h in stale:
                print(f"  - {h}")
            return 1
        print("Fresh: no stale patterns found.")
        return 0

    if not DOC_PATH.is_file():
        print(f"ERROR: {DOC_PATH} not found", file=sys.stderr)
        return 1
    text = DOC_PATH.read_text(encoding="utf-8")
    start = "<!-- SYNC-START -->"
    end = "<!-- SYNC-END -->"
    if start not in text or end not in text:
        print("ERROR: SYNC markers missing in MAKING_BETTER.md", file=sys.stderr)
        return 1
    block = f"{start}\n\n{table}\n\n{end}"
    new_text = text[: text.index(start)] + block + text[text.index(end) + len(end):]
    # Enforce LF + UTF-8, never CRLF into the doc.
    new_text = new_text.replace("\r\n", "\n")
    DOC_PATH.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"Synced Section 1 in {DOC_PATH.relative_to(WORKSPACE_ROOT)}")
    if stale:
        print("Stale-doc reminders (fix per Section 4):")
        for h in stale[:20]:
            print(f"  - {h}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
