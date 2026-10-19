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
    # P0-13: persist ledger (was memory-only, lost on crash/double-drain).
    try:
        import json
        from pathlib import Path

        out = Path(__file__).resolve().parents[2] / "results" / "attempts.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"thread_id": thread_id, **_as_dict(attempt)}, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


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
        # P0-13: LAYA unavailable — rank by critic_score deterministically (was passing[0]).
        best = max(passing, key=lambda r: (float(r.get("critic_score") or 0.0), -int(r.get("retry_count") or 0)))
        return dict(best)

    def _diff_lines(patch_str: str) -> int:
        lines = (patch_str or "").splitlines()
        return sum(1 for ln in lines if (ln.startswith("+") or ln.startswith("-")) and not ln.startswith("+++") and not ln.startswith("---"))

    scored = []
    for r in passing:
        scores = judge.score_patch(
            r.get("issue_text", ""), r.get("plan", ""), r.get("patch", "")
        )
        scored.append((scores["composite"], _diff_lines(r.get("patch", "")), r))

    # P0.2: Rank passing survivors by fewest changed lines (minimal churn), then highest composite score
    scored.sort(key=lambda item: (item[1], -item[0]))
    best_score, _lines_count, winner = scored[0]

    dangers = judge.check_dangers(winner.get("patch", ""))
    # P0-13: merge verdicts (was overwrite discarding critic.py verdict).
    prior_verdict = winner.get("critic_verdict")
    prior_score = winner.get("critic_score")
    if dangers["flagged"]:
        winner["critic_verdict"] = "flagged"
        winner["critic_score"] = best_score
    else:
        winner.setdefault("critic_verdict", "approved")
        winner.setdefault("critic_score", best_score)
    winner["laya_scores"] = {**(winner.get("laya_scores") or {}), "composite": best_score, **dangers}
    winner["arbitration"] = {
        "candidates": len(passing),
        "winner_strategy": winner.get("strategy", "default"),
        "composite": best_score,
        "prior_verdict": prior_verdict,
        "prior_score": prior_score,
    }
    return winner
