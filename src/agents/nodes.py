"""
ISHA Agent Nodes — Individual steps in the agentic loop.

Each function takes AgentState in and returns an updated AgentState.
Implemented in Phase 3.
"""

from src.agents.state import AgentState


def planner_node(state: AgentState) -> AgentState:
    """Generate a structured fix plan from the issue and repo context."""
    # TODO: Implement in Phase 3
    return state


def regression_test_node(state: AgentState) -> AgentState:
    """Write a failing test that reproduces the bug (red -> green)."""
    # TODO: Implement in Phase 3
    return state


def coder_node(state: AgentState) -> AgentState:
    """Generate a unified-diff patch to fix the bug."""
    # TODO: Implement in Phase 3
    return state


def sandbox_node(state: AgentState) -> AgentState:
    """Run tests in an isolated sandbox and capture output."""
    # TODO: Implement in Phase 3
    return state
