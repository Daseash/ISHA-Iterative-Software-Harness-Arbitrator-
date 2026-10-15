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
    conn = sqlite3.connect(str(p))
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
