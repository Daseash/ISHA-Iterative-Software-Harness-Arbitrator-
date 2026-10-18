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


def _model_suffix(name: str) -> str:
    # store rows carry the provider-prefixed id as used ('gemini/gemini-…');
    # callers pass defaults in either form — compare by final path segment.
    return (name or "").rsplit("/", 1)[-1].lower()


def model_pick(
    instance_id: str,
    repo: str,
    strategy: str,
    default: str,
    min_graded: int = 4,
    epsilon: float | None = None,
    path: Path | None = None,
) -> str:
    """Phase-0 model-axis bandit for one (org, strategy): returns '' to keep
    `default`, else the model whose Laplace reward beats it on graded rows.

    Needs >= min_graded graded rows for the (org, strategy) pair AND a
    strictly better reward than `default`'s own (0 attempt counts as 1/2).
    Never collapses candidate diversity: each strategy picks its own model.
    """
    import os
    import random

    if not (strategy and default):
        return ""
    scaled = epsilon if epsilon is not None else None
    eps = scaled if scaled is not None else float(os.getenv("ISHA_BANDIT_EPSILON", "0.15"))
    if eps > 0 and random.random() < eps:
        return ""  # exploration keeps the configured ladder authoritative
    org = org_of(instance_id, repo)
    conn = _connect(path)
    try:
        rows = conn.execute(
            "SELECT model, resolved FROM outcomes "
            "WHERE repo_org=? AND strategy=? AND resolved IS NOT NULL AND model<>''",
            (org, strategy),
        ).fetchall()
    finally:
        conn.close()
    by_model: dict[str, dict[str, int]] = {}
    for name, resolved in rows:
        slot = by_model.setdefault(
            _model_suffix(name), {"wins": 0, "graded": 0, "raw": name}
        )
        slot["graded"] += 1
        slot["wins"] += 1 if int(resolved or 0) == 1 else 0
    if not by_model:
        return ""
    total_graded = sum(v["graded"] for v in by_model.values())
    if total_graded < min_graded:
        return ""

    best = None
    best_reward = -1.0
    for suffix, slot in by_model.items():
        reward = (slot["wins"] + 1) / (slot["graded"] + 2)
        if reward > best_reward:
            best, best_reward = suffix, reward
    if not best or best == _model_suffix(default):
        return ""
    default_slot = by_model.get(_model_suffix(default), {"wins": 0, "graded": 0})
    default_reward = (default_slot["wins"] + 1) / (default_slot["graded"] + 2)
    if best_reward > default_reward:
        return by_model[best]["raw"]
    return ""


def org_critic_threshold(
    instance_id: str,
    repo: str,
    min_graded: int = 8,
    path: Path | None = None,
) -> float | None:
    """Phase-0 per-org critic threshold from graded outcomes (memory.db).

    Balanced-accuracy-optimal cut over archived (critic_score, resolved)
    pairs for the org. Returns None when either class or enough rows are
    missing — caller keeps the global 0.4 gate.
    """
    import os

    switch = str(os.getenv("ISHA_CRITIC_PER_ORG", "0")).strip().lower()
    if switch not in {"1", "true", "on"}:
        return None
    org = org_of(instance_id, repo)
    if not org:
        return None
    conn = _connect(path)
    try:
        rows = conn.execute(
            "SELECT critic_score, resolved FROM outcomes "
            "WHERE repo_org=? AND critic_score IS NOT NULL AND resolved IS NOT NULL",
            (org,),
        ).fetchall()
    finally:
        conn.close()
    if not rows or len(rows) < min_graded:
        return None
    probs = [float(r[0]) for r in rows]
    labels = [1 if int(r[1] or 0) == 1 else 0 for r in rows]
    if len(set(labels)) < 2:
        return None
    from src.review.calibration import find_threshold

    return float(find_threshold(probs, labels)["threshold"])
