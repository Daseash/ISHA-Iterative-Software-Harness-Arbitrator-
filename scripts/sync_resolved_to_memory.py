"""
Sync resolved (and graded) SWE-bench instances into ISHA memory.

This synchronizes:
1. SQLite (data/memory.db):
   - Enriches all 76 resolved=1 instances with full repo, repo_org, issue_hash,
     patch_hash, strategy, model, critic_score, and tests_passed=1.
   - Enriches all 108 resolved=0 instances with full metadata so negative veto
     has complete Docker ground-truth context.
2. Fix Ledger (output/fix_history.jsonl):
   - Writes all 76 verified resolved patches (with full issue, plan, winning patch,
     verdict="RESOLVED", tests="PASSED", score=1.0, and vector embeddings).
   - Writes the failed attempts so _mem_negative_veto can fire NEVER-DO against
     repeating proven failed patches.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
OUTPUT_DIR = ROOT / "output"
SWEBENCH_LITE = DATA_DIR / "swebench_lite.json"
ALL_PREDS = RESULTS_DIR / "all_preds.jsonl"
FIX_HISTORY = OUTPUT_DIR / "fix_history.jsonl"
DB_PATH = DATA_DIR / "memory.db"


def hash_text(text: str) -> str:
    return hashlib.sha1((text or "").encode("utf-8")).hexdigest()


def org_of(iid: str, repo: str) -> str:
    if iid and "__" in iid:
        return iid.split("__", 1)[0].lower()
    parts = [x for x in str(repo or "").replace("\\", "/").split("/") if x]
    return (parts[-1] if parts else "").lower()


def sync_all():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.rag.indexer import embed_text

    print(f"=== Syncing Resolved & Graded Instances to ISHA Memory ===")

    # 1. Load benchmark dataset (300 records)
    if not SWEBENCH_LITE.is_file():
        raise FileNotFoundError(f"Missing {SWEBENCH_LITE}")
    bench_records = {r["instance_id"]: r for r in json.loads(SWEBENCH_LITE.read_text(encoding="utf-8"))}
    print(f"[1/5] Loaded {len(bench_records)} benchmark records from {SWEBENCH_LITE.name}")

    # 2. Load all predictions (213 patches)
    preds = {}
    if ALL_PREDS.is_file():
        for line in ALL_PREDS.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                iid = row.get("instance_id")
                patch = row.get("model_patch", "")
                if iid and patch:
                    preds[iid] = patch
            except Exception:
                continue
    print(f"[2/5] Loaded {len(preds)} patches from {ALL_PREDS.name}")

    # 3. Connect to SQLite memory.db
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    db_resolved = {r[0] for r in conn.execute("SELECT instance_id FROM outcomes WHERE resolved=1").fetchall()}
    db_failed = {r[0] for r in conn.execute("SELECT instance_id FROM outcomes WHERE resolved=0").fetchall()}
    print(f"[3/5] Memory DB currently tracks {len(db_resolved)} resolved and {len(db_failed)} failed instances")

    # 4. Gather run artifacts (meta.json, plan.md, patch.diff)
    run_meta = {}
    run_plan = {}
    for p in RESULTS_DIR.glob("*/*/meta.json"):
        iid = p.parent.name
        if iid not in run_meta:
            try:
                run_meta[iid] = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    for p in RESULTS_DIR.glob("*/*/plan.md"):
        iid = p.parent.name
        if iid not in run_plan:
            try:
                run_plan[iid] = p.read_text(encoding="utf-8")
            except Exception:
                pass

    # 5. Read existing fix_history.jsonl to merge
    existing_entries = []
    seen_iids = set()
    if FIX_HISTORY.is_file():
        for line in FIX_HISTORY.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                existing_entries.append(e)
                if e.get("instance_id"):
                    seen_iids.add(e["instance_id"])
            except Exception:
                continue

    # 6. Build enriched entries and updates
    resolved_synced = 0
    failed_synced = 0
    new_ledger_entries = []

    # Process all resolved instances
    for iid in sorted(db_resolved):
        b = bench_records.get(iid, {})
        issue = b.get("problem_statement", "")
        repo = b.get("repo", "")
        org = org_of(iid, repo)

        patch = preds.get(iid, "")
        if not patch:
            patch_file = list(RESULTS_DIR.glob(f"*/{iid}/patch.diff"))
            if patch_file:
                patch = patch_file[0].read_text(encoding="utf-8")

        plan = run_plan.get(iid, "")
        meta = run_meta.get(iid, {})
        sel = meta.get("selected_candidate") or {}
        strategy = sel.get("strategy") or "minimal_diff"
        model = sel.get("model") or "gemini/gemini-3.5-flash-lite"
        score = float(sel.get("laya_combined") or 1.0)

        # Update SQLite outcomes
        conn.execute(
            """UPDATE outcomes SET
               repo = ?, repo_org = ?, issue_hash = ?, strategy = ?,
               model = ?, patch_hash = ?, critic_score = ?, tests_passed = 1,
               resolved = 1, ts = ?
               WHERE instance_id = ?""",
            (
                repo or f"repos/{org}",
                org,
                hash_text(issue),
                strategy,
                model,
                hash_text(patch),
                score if score > 0 else 1.0,
                time.time(),
                iid,
            ),
        )
        resolved_synced += 1

        # Ledger entry for fix_history
        if patch.strip() and issue.strip():
            digest = hashlib.sha1(f"{issue}::{patch}".encode("utf-8")).hexdigest()
            entry = {
                "id": str(uuid.uuid4()),
                "digest": digest,
                "ts": time.time(),
                "repo": repo or f"repos/{org}",
                "instance_id": iid,
                "issue": issue[:1200],
                "plan": plan[:800],
                "patch": patch[:4000],
                "verdict": "RESOLVED",
                "score": round(score if score > 0 else 1.0, 4),
                "tests": "PASSED",
                "strategy": strategy,
                "vector": embed_text(f"{issue} {plan}"),
            }
            new_ledger_entries.append(entry)

    # Process failed instances
    for iid in sorted(db_failed):
        b = bench_records.get(iid, {})
        issue = b.get("problem_statement", "")
        repo = b.get("repo", "")
        org = org_of(iid, repo)

        patch = preds.get(iid, "")
        if not patch:
            patch_file = list(RESULTS_DIR.glob(f"*/{iid}/patch.diff"))
            if patch_file:
                patch = patch_file[0].read_text(encoding="utf-8")

        plan = run_plan.get(iid, "")
        meta = run_meta.get(iid, {})
        sel = meta.get("selected_candidate") or {}
        strategy = sel.get("strategy") or "minimal_diff"
        model = sel.get("model") or "gemini/gemini-3.5-flash-lite"

        conn.execute(
            """UPDATE outcomes SET
               repo = ?, repo_org = ?, issue_hash = ?, strategy = ?,
               model = ?, patch_hash = ?, critic_score = ?, tests_passed = 0,
               resolved = 0, ts = ?
               WHERE instance_id = ?""",
            (
                repo or f"repos/{org}",
                org,
                hash_text(issue),
                strategy,
                model,
                hash_text(patch),
                0.0,
                time.time(),
                iid,
            ),
        )
        failed_synced += 1

        if patch.strip() and issue.strip():
            digest = hashlib.sha1(f"{issue}::{patch}".encode("utf-8")).hexdigest()
            entry = {
                "id": str(uuid.uuid4()),
                "digest": digest,
                "ts": time.time(),
                "repo": repo or f"repos/{org}",
                "instance_id": iid,
                "issue": issue[:1200],
                "plan": plan[:800],
                "patch": patch[:4000],
                "verdict": "FAILED",
                "score": 0.0,
                "tests": "FAILED",
                "strategy": strategy,
                "vector": embed_text(f"{issue} {plan}"),
            }
            new_ledger_entries.append(entry)

    conn.commit()
    conn.close()

    # 7. Merge ledger entries
    # Keep non-benchmark test rows, but replace any old benchmark stubs with enriched entries
    merged_ledger = []
    new_by_iid = {e["instance_id"]: e for e in new_ledger_entries if e.get("instance_id")}

    for e in existing_entries:
        iid = e.get("instance_id")
        if iid and iid in new_by_iid:
            continue  # Replaced by fresh enriched entry
        merged_ledger.append(e)

    for e in new_ledger_entries:
        merged_ledger.append(e)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp_ledger = FIX_HISTORY.with_suffix(".tmp")
    with open(tmp_ledger, "w", encoding="utf-8") as f:
        for e in merged_ledger:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    tmp_ledger.replace(FIX_HISTORY)

    print(f"[4/5] SQLite data/memory.db updated:")
    print(f"      - {resolved_synced} resolved=1 outcomes enriched")
    print(f"      - {failed_synced} resolved=0 outcomes enriched")
    print(f"[5/5] output/fix_history.jsonl rewritten with {len(merged_ledger)} total entries:")
    print(f"      - {len([e for e in merged_ledger if e.get('verdict') == 'RESOLVED'])} verified RESOLVED entries")
    print(f"      - {len([e for e in merged_ledger if e.get('verdict') == 'FAILED'])} verified FAILED entries (for veto)")
    print(f"=== Memory Synchronization 100% Complete! ===")


if __name__ == "__main__":
    sync_all()
