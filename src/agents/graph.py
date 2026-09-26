"""
ISHA LangGraph — State machine orchestration for the agentic loop.

Wires planner -> regression_test -> coder -> sandbox -> critic into a
cyclic state graph with conditional retry logic.
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.agents.nodes import (
    coder_node,
    planner_node,
    regression_test_node,
    sandbox_node,
)
from src.agents.state import AgentState
from src.review.critic import critic_node

MAX_RETRIES = 3


def _route_after_sandbox(state: AgentState) -> str:
    """Retry the coder while tests fail and budget remains, else review."""
    failed = "FAILED" in (state.test_output or "")
    if failed and state.retry_count < MAX_RETRIES:
        return "coder"
    return "critic"


def build_graph():
    """Compile and return the single-agent ISHA state graph."""
    workflow = StateGraph(AgentState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("regression_test", regression_test_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("sandbox", sandbox_node)
    workflow.add_node("critic", critic_node)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "regression_test")
    workflow.add_edge("regression_test", "coder")
    workflow.add_edge("coder", "sandbox")
    workflow.add_conditional_edges(
        "sandbox",
        _route_after_sandbox,
        {"coder": "coder", "critic": "critic"},
    )
    workflow.add_edge("critic", END)

    return workflow.compile(checkpointer=MemorySaver())


compiled_graph = build_graph()


def run_issue(issue_text: str, repo_path: str = "tests/dummy_repo", thread_id: str = "1") -> AgentState:
    """Convenience wrapper: build state, invoke the graph, return the result."""
    from src.agents.context import build_repo_context

    state = AgentState(
        issue_text=issue_text,
        repo_path=repo_path,
        repo_context=build_repo_context(issue_text, repo_path),
    )
    result = compiled_graph.invoke(
        state, config={"configurable": {"thread_id": thread_id}}
    )
    if isinstance(result, dict):
        result = AgentState(**result)
    return result
