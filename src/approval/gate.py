"""
ISHA Human Approval Gate — Pause for human sign-off on flagged diffs.

Uses LangGraph interrupt() to pause and resume. Logs all decisions
to an audit trail. Implemented in Phase 7.
"""

from src.agents.state import AgentState


def approval_node(state: AgentState) -> AgentState:
    """Pause for human approval if the diff was flagged by LAYA."""
    # TODO: Implement with LangGraph interrupt() in Phase 7
    return state
