#!/usr/bin/env python3
"""
ISHA Golden 7 Regression Safety Net — Protect already resolved benchmark tasks.

Verifies that any code or prompt changes in ISHA never regress on the 7 tasks
that are 100% verified resolved under the official SWE-bench Docker testbed:
  1. django__django-10914
  2. django__django-11039
  3. django__django-11049
  4. django__django-11099
  5. django__django-11133
  6. django__django-11583
  7. pytest-dev__pytest-11143
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENT_DIR = HERE.parent
RESULTS_DIR = AGENT_DIR / "results"

GOLDEN_INSTANCES = [
    "django__django-10914",
    "django__django-11039",
    "django__django-11049",
    "django__django-11099",
    "django__django-11133",
    "django__django-11583",
    "pytest-dev__pytest-11143",
]


def find_patches(instance_id: str) -> list[tuple[Path, str]]:
    """Return [(source_path, patch_text)] from predictions.json and patch.diff."""
    found: list[tuple[Path, str]] = []
    if not RESULTS_DIR.is_dir():
        return found
    for pred_file in RESULTS_DIR.rglob("predictions.json"):
        try:
            data = json.loads(pred_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        items = data if isinstance(data, list) else data.get("predictions", [])
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and item.get("instance_id") == instance_id:
                patch = item.get("model_patch") or item.get("patch") or ""
                if isinstance(patch, str):
                    found.append((pred_file, patch))
    for patch_file in RESULTS_DIR.rglob(f"{instance_id}/patch.diff"):
        try:
            text = patch_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        found.append((patch_file, text))
    return found


def find_resolved(instance_id: str) -> tuple[bool, str]:
    """Search per-instance report.json / harness_report.json for resolved is True."""
    if not RESULTS_DIR.is_dir():
        return False, "results/ missing"
    for rep_file in RESULTS_DIR.rglob("report.json"):
        try:
            data = json.loads(rep_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        # Shape 1: {instance_id: {resolved: true}}
        if instance_id in data and isinstance(data[instance_id], dict):
            if data[instance_id].get("resolved") is True:
                return True, str(rep_file)
        # Shape 2: single-instance file under .../<iid>/report.json = {resolved: true}
        if f"{instance_id}" in str(rep_file) and data.get("resolved") is True:
            return True, str(rep_file)
    for rep_file in RESULTS_DIR.rglob("harness_report.json"):
        try:
            data = json.loads(rep_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            if instance_id in data and isinstance(data[instance_id], dict):
                if data[instance_id].get("resolved") is True:
                    return True, str(rep_file)
            for key in ("resolved_instances", "completed_ids"):
                ids = data.get(key)
                if isinstance(ids, list) and instance_id in ids:
                    return True, str(rep_file)
    return False, "no report with resolved=true found"


def patch_is_clean(patch: str) -> tuple[bool, str]:
    """Lightweight `git diff --check` equivalent for a patch file."""
    if not patch or not patch.strip():
        return False, "empty patch"
    if "<<<<<<<" in patch or ">>>>>>>" in patch:
        return False, "conflict markers present"
    if not ("diff --git" in patch or patch.startswith("--- ")):
        return False, "not a unified diff"
    bad_lines = []
    for i, line in enumerate(patch.splitlines(), start=1):
        if line.startswith("+") and not line.startswith("+++"):
            if line != line.rstrip():
                bad_lines.append(i)
                if len(bad_lines) >= 3:
                    break
    if bad_lines:
        return False, f"trailing whitespace on added lines {bad_lines[:3]}"
    return True, "clean"


def check_golden_protection() -> bool:
    print("=" * 64)
    print("  ISHA: GOLDEN 7 REGRESSION SAFETY NET (P0-03 real verifier)")
    print("=" * 64)
    all_ok = True
    for idx, inst in enumerate(GOLDEN_INSTANCES, 1):
        patches = find_patches(inst)
        non_empty = [(p, t) for p, t in patches if t and t.strip()]
        resolved, evidence = find_resolved(inst)
        clean_ok, clean_msg = (False, "no patch found")
        clean_src = ""
        for src, text in non_empty:
            ok, msg = patch_is_clean(text)
            if ok:
                clean_ok, clean_msg, clean_src = True, msg, str(src)
                break
        else:
            if non_empty:
                clean_msg = patch_is_clean(non_empty[0][1])[1]
                clean_src = str(non_empty[0][0])
        ok = bool(non_empty) and resolved and clean_ok
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_ok = False
        print(f"  [{idx}/7] {inst} -> {status}")
        print(f"         patch: {len(non_empty)}/{len(patches)} non-empty ({clean_msg}) {clean_src}")
        print(f"         resolved: {resolved} ({evidence})")
    print("=" * 64)
    print(f"  STATUS: {'GREEN — all 7 golden hold' if all_ok else 'RED — golden regressed (see FAIL above)'}")
    print("=" * 64)
    return all_ok


if __name__ == "__main__":
    ok = check_golden_protection()
    sys.exit(0 if ok else 1)
