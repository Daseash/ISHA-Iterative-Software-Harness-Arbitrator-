"""P0-11 core: low_quality needs explicit approval (A-5 strictness)."""

from src.agents.graph import merger_node
from src.agents.state import AgentState


def test_low_quality_not_auto_approved():
    st = AgentState(
        issue_text="b",
        repo_path="/tmp",
        patch="diff",
        test_output="PASSED",
        critic_verdict="low_quality",
        critic_score=0.5,
        strategy="minimal_diff",
    )
    out = merger_node(st, config={"configurable": {"thread_id": "t-p011", "apply": False}})
    assert out.approved is None or out.approved is False
    assert out.critic_verdict == "low_quality"


def test_approved_auto_clears():
    st = AgentState(
        issue_text="b",
        repo_path="/tmp",
        patch="diff",
        test_output="PASSED",
        critic_verdict="approved",
        critic_score=0.9,
        strategy="minimal_diff",
    )
    out = merger_node(st, config={"configurable": {"thread_id": "t-p011b", "apply": False}})
    assert out.approved is True
