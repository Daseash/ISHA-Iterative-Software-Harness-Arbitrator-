"""
ISHA Multi-Agent Dispatch — Fan-out to N isolated agent attempts.

Uses LangGraph Send() to spawn independent agents, each with its own
git worktree and patching strategy.
"""

from copy import deepcopy

from src.agents.state import AgentState

ALL_STRATEGIES = [
    "minimal_diff",
    "root_cause_first",
    "call_site_aware",
    "defensive_fix",
    "cross_file_audit",
]
STRATEGIES = ["minimal_diff", "call_site_aware", "root_cause_first"]


def select_tournament_strategies(state: AgentState | dict) -> list[str]:
    """Subsystem 5: 3-of-5 Strategy Selector based on AST & Traceback profile.

    Slot 1: minimal_diff (surgical line edits, early returns).
    Slot 2: call_site_aware / root_cause_first (repairs underlying invariant).
    Slot 3: defensive_fix if NoneType/KeyError/IndexError/AttributeError in trace,
            cross_file_audit on multi-module dependency bugs,
            else call_site_aware.
    """
    s1 = "minimal_diff"
    s2 = "root_cause_first"

    if hasattr(state, "issue_text"):
        issue_text = getattr(state, "issue_text", "") or ""
        test_output = getattr(state, "test_output", "") or ""
        blast = getattr(state, "blast_radius", {}) or {}
    else:
        issue_text = state.get("issue_text", "") or ""
        test_output = state.get("test_output", "") or ""
        blast = state.get("blast_radius", {}) or {}

    text = f"{issue_text} {test_output}".lower()
    callers = int(blast.get("callers", 0) or 0)

    if any(k in text for k in ("nonetype", "keyerror", "indexerror", "attributeerror")):
        s3 = "defensive_fix"
    elif any(k in text for k in ("multi-module", "cross_file", "cross-file", "submodule")):
        s3 = "cross_file_audit"
    elif callers > 5:
        s3 = "call_site_aware"
    else:
        s3 = "call_site_aware"

    return [s1, s3, s2]


def dispatch_agents(state: AgentState):
    """Fan out to 3 independent agents with selected tournament strategies."""
    from langgraph.types import Send

    from src.tools.worktree_manager import create_worktree

    base = deepcopy(state.model_dump() if hasattr(state, "model_dump") else dict(state))
    iid = (base.get("instance_id") or "local").replace("/", "_")[:40]
    retry = base.get("retry_count", 0)

    # Subsystem 5: Select 3 of 5 strategies dynamically
    selected = select_tournament_strategies(state)
    order = selected
    try:
        from src.memory.store import strategy_order

        order = strategy_order(base.get("instance_id") or "", base.get("repo") or "", strategies=selected)
    except Exception:
        order = selected
    sends = []
    from src.agents.candidates import strategy_models
    assigned_models = strategy_models()

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

        candidate_model = assigned_models.get(strategy, "")
        payload = {
            **base,
            "worktree": worktree,
            "strategy": strategy,
            "assigned_model": candidate_model,
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
            "repro_valid": base.get("repro_valid"),
            "repro_ok": base.get("repro_ok"),
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
