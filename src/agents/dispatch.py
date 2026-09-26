"""
ISHA Multi-Agent Dispatch — Fan-out to N isolated agent attempts.

Uses LangGraph Send() to spawn independent agents, each with its own
git worktree and patching strategy.
"""

from src.agents.state import AgentState

STRATEGIES = ["minimal_diff", "call_site_aware", "alt_test_phrasing"]


def dispatch_agents(state: AgentState):
    """Fan out to 3 independent agents with different strategies."""
    from langgraph.types import Send

    from src.tools.worktree_manager import create_worktree

    base = state.model_dump() if hasattr(state, "model_dump") else dict(state)
    sends = []
    for i, strategy in enumerate(STRATEGIES, start=1):
        try:
            worktree = create_worktree(state.repo_path, f"agent-{i}")
        except Exception as exc:
            # Fall back to a sandbox copy so fan-out never dies.
            from src.tools.sandbox import make_sandbox

            worktree = make_sandbox(state.repo_path, prefix=f"isha-agent-{i}-")
            _ = exc

        payload = {
            **base,
            "worktree": worktree,
            "strategy": strategy,
            "retry_count": 0,
            "test_output": "",
            "patch": "",
            "critic_verdict": None,
            "critic_score": 0.0,
            "laya_scores": {},
        }
        # Distinct node names per branch keep the fan-out parallel — LangGraph
        # dedupes pull tasks by node name, so shared names would serialise.
        sends.append(Send(f"attempt{i}", payload))
    return sends
