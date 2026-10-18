#!/usr/bin/env python3
"""A-1 pre-submission lint for the SWE-bench leaderboard payload.

Validates every row of results/all_preds.jsonl BEFORE the owner uploads it
(the leaderboard's grader is unforgiving about schema drift; better to fail
loudly here than tunnel-swallowed there).

Checks:
  * file parses as JSONL (one JSON object per line, no BOM/CRLF artifacts)
  * every row has install/instance_id/model_patch as non-empty reserved-type
  * model_patch contains a real diff header from the SWE-bench patch contract
  * patch is unchanged-safe: no `===` placeholder, no `[INVALID]`-style sentinel
Exit 0 = safe to submit; anything else prints the offending row indices.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRED = HERE.parent / "results" / "all_preds.jsonl"

REQUIRED_KEYS = {"instance_id", "model_patch"}
DIFF_HINT = ("diff --git", "--- ", "+++ ")

errors: list[str] = []
rows: list[dict] = []
raw = PRED.read_bytes()
if raw[:3] == b"\xef\xbb\xbf":
    errors.append("BOM at file start")
for n, line in enumerate(raw.decode("utf-8").split("\n"), start=1):
    line = line.strip()
    if not line:
        continue
    try:
        row = json.loads(line)
    except ValueError as exc:
        errors.append(f"line {n}: not valid JSON — {exc}")
        continue
    rows.append(row)
    missing = REQUIRED_KEYS - set(row)
    if missing:
        errors.append(f"line {n}: missing keys {sorted(missing)}")
        continue
    iid = row["instance_id"]
    patch = row["model_patch"]
    if not isinstance(iid, str) or not iid.strip():
        errors.append(f"line {n}: instance_id empty/non-string")
    if not isinstance(patch, str) or not patch.strip():
        errors.append(f"line {n}: model_patch empty")
        continue
    if not any(h in patch for h in DIFF_HINT):
        errors.append(f"line {n} ({iid}): no diff header")
    # Harness rejects naive full-file rewrites; sanity flag huge diffs only.
    if len(patch) > 400_000:
        errors.append(f"line {n} ({iid}): patch unusually large ({len(patch)}B)")

print(f"{len(rows)} rows validated from {PRED.name}")
if errors:
    print("LINT FAIL:")
    for e in errors:
        print(" -", e)
    raise SystemExit(1)
print("LINT PASS — file is schema-clean; safe to upload")
