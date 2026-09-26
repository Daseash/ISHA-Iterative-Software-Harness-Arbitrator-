"""
ISHA Arbitration — Picks the best attempt from parallel agents.

Uses LAYA composite scores to rank passing attempts and select a winner.
Implemented in Phase 4 + Phase 6.
"""


def arbitration_node(results: list) -> dict:
    """Rank all passing attempts by LAYA score, pick the winner."""
    # TODO: Implement with LayaJudge in Phase 4
    if results:
        return results[0] if isinstance(results[0], dict) else results[0].dict()
    return {}
