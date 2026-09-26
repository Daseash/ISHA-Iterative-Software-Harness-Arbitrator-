"""
ISHA Arbitration — Picks the best attempt from parallel agents.

Uses LAYA composite scores to rank passing attempts and select a winner.
"""

from src.review.laya_judge import get_judge


def arbitration_node(results: list) -> dict:
    """Rank all passing attempts by LAYA score, pick the winner."""
    if not results:
        return {}

    def _as_dict(item) -> dict:
        if isinstance(item, dict):
            return item
        if hasattr(item, "model_dump"):
            return item.model_dump()
        if hasattr(item, "dict"):
            return item.dict()
        return dict(item)

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
        scores = judge.score_patch(r.get("issue_text", ""), r.get("plan", ""), r.get("patch", ""))
        scored.append((scores["composite"], r))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    best_score, winner = scored[0]

    dangers = judge.check_dangers(winner.get("patch", ""))
    winner["critic_verdict"] = "flagged" if dangers["flagged"] else "approved"
    winner["critic_score"] = best_score
    winner["laya_scores"] = {"composite": best_score, **dangers}
    return winner
