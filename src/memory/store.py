"""ISHA memory store — closed-loop outcomes (P0-05 / Sec 6).

Write-A (fast): insert attempt with resolved=NULL from record_fix path.
Write-B (truth): UPDATE resolved + fail_bucket after Docker grades in harness_eval.
JSONL ledger remains as export only; SQLite is the queryable truth.
"""

from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS outcomes(
  instance_id TEXT PRIMARY KEY,
  repo TEXT NOT NULL,
  repo_org TEXT NOT NULL,
  issue_hash TEXT NOT NULL,
  strategy TEXT NOT NULL,
  model TEXT NOT NULL,
  patch_hash TEXT NOT NULL,
  critic_score REAL NOT NULL,
  tests_passed INTEGER NOT NULL,
  resolved INTEGER,
  fail_bucket TEXT,
  traceback_sig TEXT,
  ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_org ON outcomes(repo_org);
CREATE INDEX IF NOT EXISTS idx_resolved ON outcomes(resolved);
"""


def db_path() -> Path:
    import os

    override = os.getenv("ISHA_MEMORY_DB", "")
    if override:
        p = Path(override)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    root = Path(__file__).resolve().parents[2]
    p = root / "data" / "memory.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _connect(path: Path | None = None) -> sqlite3.Connection:
    p = path or db_path()
    conn = sqlite3.connect(str(p), timeout=60.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(SCHEMA)
    return conn


def org_of(instance_id: str, repo: str) -> str:
    if instance_id and "__" in instance_id:
        return instance_id.split("__", 1)[0].lower()
    # filesystem repo like "repos/django" -> first meaningful component
    parts = [x for x in str(repo or "").replace("\\", "/").split("/") if x]
    return (parts[-1] if parts else "").lower()


def hash_text(text: str) -> str:
    return hashlib.sha1((text or "").encode("utf-8")).hexdigest()


def record_attempt(
    instance_id: str,
    repo: str,
    issue: str,
    strategy: str,
    model: str,
    patch: str,
    critic_score: float,
    tests_passed: bool,
    fail_bucket: str = "",
    traceback_sig: str = "",
    path: Path | None = None,
) -> bool:
    """Write-A: insert attempt, resolved=NULL. Returns False if already present."""
    iid = (instance_id or "").strip() or f"local-{hash_text(repo + issue + patch)[:12]}"
    conn = _connect(path)
    try:
        conn.execute(
            """INSERT OR IGNORE INTO outcomes(
            instance_id, repo, repo_org, issue_hash, strategy, model,
            patch_hash, critic_score, tests_passed, resolved,
            fail_bucket, traceback_sig, ts)
            VALUES (?,?,?,?,?,?,?,?,?,?,?, ?, ?)""",
            (
                iid,
                repo or "",
                org_of(iid, repo),
                hash_text(issue or ""),
                strategy or "",
                model or "",
                hash_text(patch or ""),
                float(critic_score or 0.0),
                1 if tests_passed else 0,
                None,
                fail_bucket or "",
                traceback_sig or "",
                time.time(),
            ),
        )
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def resolve(
    instance_id: str,
    resolved: bool,
    fail_bucket: str = "",
    traceback_sig: str = "",
    path: Path | None = None,
) -> bool:
    """Write-B: set Docker truth for an instance. Inserts stub row if missing."""
    iid = (instance_id or "").strip()
    if not iid:
        return False
    conn = _connect(path)
    try:
        cur = conn.execute("SELECT instance_id FROM outcomes WHERE instance_id=?", (iid,))
        exists = cur.fetchone() is not None
        if exists:
            if traceback_sig:
                conn.execute(
                    "UPDATE outcomes SET resolved=?, fail_bucket=?, traceback_sig=? WHERE instance_id=?",
                    (1 if resolved else 0, fail_bucket or "", traceback_sig, iid),
                )
            else:
                conn.execute(
                    "UPDATE outcomes SET resolved=?, fail_bucket=? WHERE instance_id=?",
                    (1 if resolved else 0, fail_bucket or "", iid),
                )
        else:
            conn.execute(
                """INSERT INTO outcomes(instance_id, repo, repo_org, issue_hash, strategy,
                model, patch_hash, critic_score, tests_passed, resolved, fail_bucket, traceback_sig, ts)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (iid, "", org_of(iid, ""), "", "", "", "", 0.0, 0,
                 1 if resolved else 0, fail_bucket or "", traceback_sig or "", time.time()),
            )
        conn.commit()
        return True
    finally:
        conn.close()


def fetch(instance_id: str, path: Path | None = None) -> dict | None:
    conn = _connect(path)
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM outcomes WHERE instance_id=?", (instance_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def strategy_order(
    instance_id: str,
    repo: str = "",
    strategies: list[str] | None = None,
    epsilon: float | None = None,
    path: Path | None = None,
) -> list[str]:
    """AR-5: rank fan-out strategies by smoothed reward from graded outcomes.

    reward = (wins + 1) / (graded + 2), Laplace-smoothed so unseen strategies
    stay in the race (1/2) instead of getting starved. Only graded rows count;
    attempts without a verdict (resolved NULL) are deliberately ignored so a
    wave of ungraded solves cannot re-rank anything.

    Exploration epsilon (<1, ISHA_BANDIT_EPSILON, default 0.15) shuffles the
    order with that probability — reorders, never drops a strategy.
    """
    import os
    import random

    strs = list(strategies or ["minimal_diff", "call_site_aware", "root_cause_first"])
    eps = epsilon if epsilon is not None else float(os.getenv("ISHA_BANDIT_EPSILON", "0.15"))
    if eps >= 1.0 or random.random() < eps:
        random.shuffle(strs)
        return strs

    org = org_of(instance_id, repo)
    conn = _connect(path)
    try:
        placeholders = ",".join("?" for _ in strs)
        cur = conn.execute(
            f"SELECT strategy, SUM(resolved), COUNT(resolved) FROM outcomes "
            f"WHERE repo_org=? AND strategy IN ({placeholders}) "
            f"AND resolved IS NOT NULL GROUP BY strategy",
            [org, *strs],
        )
        stats = {row[0]: (int(row[1] or 0), int(row[2] or 0)) for row in cur.fetchall()}
    finally:
        conn.close()

    def _score(name: str) -> float:
        wins, graded = stats.get(name, (0, 0))
        return (wins + 1) / (graded + 2)

    return sorted(strs, key=_score, reverse=True)
