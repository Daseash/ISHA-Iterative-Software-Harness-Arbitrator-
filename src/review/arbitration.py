"""
ISHA Arbitration — Picks the best attempt from parallel agents.

Branches fan-in here through an attempt ledger: every critic registers its
result, then LAYA composite scores pick the winner.
"""

import threading

from src.review.laya_judge import get_judge

_LEDGER: dict = {}
_LOCK = threading.Lock()


def record_attempt(thread_id: str, attempt: dict) -> None:
    """Register one branch's result for the arbitration fan-in."""
    with _LOCK:
        _LEDGER.setdefault(thread_id, []).append(attempt)


def collect_attempts(thread_id: str) -> list:
    """Drain and return all recorded attempts for a thread."""
    with _LOCK:
        return _LEDGER.pop(thread_id, [])


def peek_attempts(thread_id: str) -> list:
    """Return recorded attempts for a thread without draining the ledger."""
    with _LOCK:
        return list(_LEDGER.get(thread_id, []))


def _as_dict(item) -> dict:
    if isinstance(item, dict):
        return item
    if hasattr(item, "model_dump"):
        return item.model_dump()
    if hasattr(item, "dict"):
        return item.dict()
    return dict(item)


def arbitration_node(results: list) -> dict:
    """Rank all passing attempts by LAYA score, pick the winner."""
    if not results:
        return {}

    attempts = [_as_dict(r) for r in results]
    passing = [r for r in attempts if "FAILED" not in (r.get("test_output") or "FAILED")]

    if not passing:
        # All failed — return the one with fewest retries.
        return min(attempts, key=lambda r: r.get("retry_count", 99))

    try:
        judge = get_judge()
    except Exception:
        # LAYA unavailable: fall back to first passing attempt.
        return passing[0]

    scored = []
    for r in passing:
        scores = judge.score_patch(
            r.get("issue_text", ""), r.get("plan", ""), r.get("patch", "")
        )
        scored.append((scores["composite"], r))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    best_score, winner = scored[0]

    dangers = judge.check_dangers(winner.get("patch", ""))
    winner["critic_verdict"] = "flagged" if dangers["flagged"] else "approved"
    winner["critic_score"] = best_score
    winner["laya_scores"] = {"composite": best_score, **dangers}
    winner["arbitration"] = {
        "candidates": len(passing),
        "winner_strategy": winner.get("strategy", "default"),
        "composite": best_score,
    }
    return winner
