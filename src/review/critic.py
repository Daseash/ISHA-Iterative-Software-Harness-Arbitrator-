"""
ISHA Critic — LAYA-powered adversarial diff reviewer.

Scores patches on quality, relevance, and safety using calibrated
probabilities instead of text-only LLM judgment.
"""

from langgraph.types import RunnableConfig

from src.agents.state import AgentState, coerce_state


def critic_node(state, config: RunnableConfig | None = None) -> AgentState:
    """Adversarial review of the patch using LAYA decision engine."""
    state = coerce_state(state)
    from src.review.laya_judge import get_judge

    try:
        judge = get_judge()

        scores = judge.score_patch(state.issue_text, state.plan, state.patch)
        state.laya_scores = scores

        dangers = judge.check_dangers(state.patch)

        if dangers["flagged"]:
            state.critic_verdict = "flagged"
        elif scores["composite"] < 0.4:
            state.critic_verdict = "low_quality"
        else:
            state.critic_verdict = "approved"
        state.critic_score = scores["composite"]
        state.laya_scores = {**scores, **dangers}
    except Exception as exc:
        state.critic_verdict = "error"
        state.critic_score = 0.0
        state.laya_scores = {"error": str(exc)}

    _record(state, config)
    return state


def _record(state: AgentState, config: dict | None) -> None:
    """Register this branch's attempt so arbitration can fan-in on it."""
    try:
        from src.review.arbitration import record_attempt

        thread_id = (
            (config or {}).get("configurable", {}).get("thread_id", "default")
        )
        record_attempt(thread_id, state.model_dump() if hasattr(state, "model_dump") else dict(state))
    except Exception:
        pass
