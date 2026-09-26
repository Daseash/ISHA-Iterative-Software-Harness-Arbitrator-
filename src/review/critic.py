"""
ISHA Critic — LAYA-powered adversarial diff reviewer.

Scores patches on quality, relevance, and safety using calibrated
probabilities instead of text-only LLM judgment. Implemented in Phase 4.
"""

from src.agents.state import AgentState


def critic_node(state: AgentState) -> AgentState:
    """Adversarial review of the patch using LAYA decision engine."""
    # TODO: Implement with LayaJudge in Phase 4
    return state
