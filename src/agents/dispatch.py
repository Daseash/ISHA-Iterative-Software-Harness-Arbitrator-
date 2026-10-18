"""
ISHA Multi-Agent Dispatch — Fan-out to N isolated agent attempts.

Uses LangGraph Send() to spawn independent agents, each with its own
git worktree and patching strategy.
"""

from copy import deepcopy

from src.agents.state import AgentState

# P0-10: must match candidates.STRATEGY_VARIANTS (was alt_test_phrasing = generic prompt).
STRATEGIES = ["minimal_diff", "call_site_aware", "root_cause_first"]


def dispatch_agents(state: AgentState):
    """Fan out to 3 independent agents with different strategies."""
    from langgraph.types import Send

    from src.tools.worktree_manager import create_worktree

    base = deepcopy(state.model_dump() if hasattr(state, "model_dump") else dict(state))
    iid = (base.get("instance_id") or "local").replace("/", "_")[:40]
    retry = base.get("retry_count", 0)
    # AR-5: order strategies by graded-outcome reward (exploratory reorder).
    order = STRATEGIES
    try:
        from src.memory.store import strategy_order

        order = strategy_order(base.get("instance_id") or "", base.get("repo") or "")
    except Exception:
        order = STRATEGIES
    sends = []
    for i, strategy in enumerate(order, start=1):
        # P0-10: unique worktree per (instance, branch, retry) — was agent-{i} (collides).
        tag = f"agent-{iid}-{i}-r{retry}"
        try:
            worktree = create_worktree(state.repo_path, tag)
        except Exception as exc:
            # Fall back to a sandbox copy so fan-out never dies.
            # P0-08: unified prefix (cleanup matches isha-sandbox-*).
            from src.tools.sandbox import make_sandbox

            worktree = make_sandbox(state.repo_path, prefix=f"isha-sandbox-{iid}-{i}-")
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
            # P0-10: fresh branch state — stale plan/escalation forced approval.
            # Deepcopied above so nested lists never cross-mutate between branches.
            "plan": base.get("plan", ""),
            "escalation": "",
            "regression_test": base.get("regression_test", ""),
            "blast_radius": dict(base.get("blast_radius") or {}),
            "localization": list(base.get("localization") or []),
            "context_notes": list(base.get("context_notes") or []),
            "candidates": [],
            "model_log": list(base.get("model_log") or []),
        }
        # Distinct node names per branch keep the fan-out parallel — LangGraph
        # dedupes pull tasks by node name, so shared names would serialise.
        sends.append(Send(f"attempt{i}", payload))
    return sends
