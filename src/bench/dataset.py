"""
ISHA SWE-bench dataset access — load, cache, slice.

The dataset is fetched once from HuggingFace and cached under ``data/`` so
every later benchmark run (and every resume of a half-finished run) sees the
exact same records without touching the network.

Two accessors exist on purpose:

  ``agent_view``   the ONLY fields the solver is allowed to see — issue text,
                   repo, base commit.  No gold patch, no test patch, no
                   FAIL_TO_PASS/PASS_TO_PASS list.
  ``full_record``  everything, used exclusively by the evaluation step and by
                   post-hoc failure analysis.

Ground rule: never hand a solver the gold patch or the test patch.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
SLICE_DIR = DATA_DIR / "slices"

DATASET_NAME = os.getenv("ISHA_BENCH_DATASET", "SWE-bench/SWE-bench_Lite")
SPLIT = os.getenv("ISHA_BENCH_SPLIT", "test")
CACHE_PATH = DATA_DIR / "swebench_lite.json"

AGENT_FIELDS = ("instance_id", "repo", "base_commit", "problem_statement", "version")


def load_records(refresh: bool = False) -> list[dict]:
    """Return every record of the benchmark split (cached on disk)."""
    if CACHE_PATH.is_file() and not refresh:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    from datasets import load_dataset

    ds = load_dataset(DATASET_NAME, split=SPLIT)
    rows = [{k: ds[i][k] for k in ds[i].keys()} for i in range(len(ds))]
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(rows, ensure_ascii=False), encoding="utf-8"
    )
    return rows


def agent_view(record: dict) -> dict:
    """Strip a record down to what the solver may see."""
    return {k: record.get(k, "") for k in AGENT_FIELDS}


def select_slice(records: list[dict], limit: int, mode: str = "head") -> list[dict]:
    """Pick a *fixed*, reproducible slice of the split.

    head        first ``limit`` records in dataset order (default — fixed and
                independent of any tuning decision)
    stratified  proportional allocation across repos, then dataset order
                inside each repo (more representative, still deterministic)
    ids         honour an explicit id list passed via ISHA_BENCH_IDS
    """
    if limit <= 0 or limit >= len(records):
        return list(records)

    if mode == "ids":
        wanted = [i.strip() for i in os.getenv("ISHA_BENCH_IDS", "").split(",") if i.strip()]
        by_id = {r["instance_id"]: r for r in records}
        return [by_id[i] for i in wanted if i in by_id]

    if mode != "stratified":
        return records[:limit]

    from collections import Counter, defaultdict

    per_repo = defaultdict(list)
    for r in records:
        per_repo[r["repo"]].append(r)

    share = Counter({repo: len(rows) for repo, rows in per_repo.items()})
    total = sum(share.values())
    quota = {repo: max(1, round(n * limit / total)) for repo, n in share.items()}

    # Grow/shrink greedily to hit the exact limit, largest remainder first.
    while sum(quota.values()) > limit:
        repo = max(quota, key=lambda r: (quota[r], share[r]))
        if quota[repo] <= 1:
            break
        quota[repo] -= 1
    while sum(quota.values()) < limit:
        repo = max(
            (r for r in per_repo if quota[r] < len(per_repo[r])),
            key=lambda r: share[r],
            default=None,
        )
        if repo is None:
            break
        quota[repo] += 1

    out: list[dict] = []
    for repo in per_repo:
        out.extend(per_repo[repo][: quota.get(repo, 0)])
    return out[:limit]


def load_slice(limit: int, mode: str | None = None, refresh: bool = False) -> list[dict]:
    mode = mode or os.getenv("ISHA_BENCH_SLICE", "head")
    return select_slice(load_records(refresh), limit, mode)


def write_slice(slice_id: str, records: list[dict]) -> Path:
    """Persist the exact instance list of a run so it can be reproduced."""
    SLICE_DIR.mkdir(parents=True, exist_ok=True)
    path = SLICE_DIR / f"{slice_id}.json"
    path.write_text(
        json.dumps([r["instance_id"] for r in records], indent=2), encoding="utf-8"
    )
    return path


def read_slice(slice_id: str) -> list[str] | None:
    path = SLICE_DIR / f"{slice_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
