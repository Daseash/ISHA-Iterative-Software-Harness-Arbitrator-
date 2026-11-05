"""
ISHA LangGraph — State machine orchestration for the agentic loop.

Wires planner -> regression_test -> coder -> sandbox -> critic into a
cyclic state graph with conditional retry logic.
"""

import os
import threading
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import RunnableConfig

from src.agents.decomposer import decomposer_node
from src.agents.investigation import investigation_node
from src.agents.nodes import (
    candidate_node,
    coder_node,
    confidence_gate_node,
    planner_node,
    regression_test_node,
    sandbox_node,
)
from src.agents.session_manager import save_session
from src.agents.state import AgentState, coerce_state, test_failed, test_passed
from src.review.critic import critic_node

MAX_RETRIES = int(os.getenv("ISHA_MAX_RETRIES", "3"))


def get_checkpointer():
    """Persistent on-disk checkpointer using SqliteSaver with fallback to MemorySaver."""
    try:
        import sqlite3
        from langgraph.checkpoint.sqlite import SqliteSaver

        conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
        saver = SqliteSaver(conn)
        saver.setup()
        return saver
    except Exception:
        return MemorySaver()


def _blast_escalation(state: AgentState) -> str:
    """Non-empty reason when fan-out demands human review regardless of critic score."""
    import os

    br = state.blast_radius or {}
    try:
        score_threshold = float(os.getenv("ISHA_BLAST_REVIEW_SCORE", "0.4"))
        caller_threshold = int(os.getenv("ISHA_BLAST_REVIEW_CALLERS", "150"))
    except ValueError:
        score_threshold, caller_threshold = 0.4, 150

    score = float(br.get("score", 0) or 0)
    callers = int(br.get("callers", 0) or 0)
    if score >= score_threshold:
        return f"blast radius {score:.2f} >= {score_threshold} — human review regardless of critic score"
    if callers >= caller_threshold:
        return f"~{callers} callers >= {caller_threshold} — human review regardless of critic score"
    return ""


def approval_node(state, config=None) -> AgentState:
    """Route flagged diffs to the human gate; clear ones skip it.

    Escalations (low planner confidence, excessive blast radius) skip the
    auto-approve path and land in human review regardless of critic score.

    Also advances to the next sub-issue when one exists. This must happen
    inside a node: LangGraph hands routers a plain dict, so mutations made
    on a coerced copy in a conditional router are silently discarded and
    the graph loops on the same sub-issue forever.
    """
    from src.approval.gate import approval_node as gate, log_approval

    state = coerce_state(state)

    if state.escalation:
        # Confidence gate fired before any patch was attempted.
        state.approved = False
        log_approval({
            "issue": state.issue_text,
            "verdict": state.critic_verdict,
            "score": state.critic_score,
            "decision": "escalated",
            "reason": state.escalation,
            "patch_preview": (state.patch or "")[:400],
        })
        return state

    state = coerce_state(gate(state, config))

    if state.approved is True:
        reason = _blast_escalation(state)
        if reason:
            state.approved = False
            log_approval({
                "issue": state.issue_text,
                "verdict": state.critic_verdict,
                "score": state.critic_score,
                "decision": "escalated_blast_radius",
                "reason": reason,
                "patch_preview": (state.patch or "")[:1200],
            })
            return state

    if state.approved is False:
        return state

    sub_issues = state.sub_issues
    if not isinstance(sub_issues, list):
        return state

    curr_idx = state.current_sub_issue_index if state.current_sub_issue_index is not None else 0
    next_idx = curr_idx + 1
    if 0 <= next_idx < len(sub_issues):
        sub_item = sub_issues[next_idx]
        if isinstance(sub_item, dict):
            sub_item["status"] = "in_progress"
            title = sub_item.get("title", f"Sub-issue {next_idx + 1}")
            desc = sub_item.get("description", "")
        else:
            title = f"Sub-issue {next_idx + 1}"
            desc = str(sub_item) if sub_item is not None else ""

        state.current_sub_issue_index = next_idx
        state.retry_count = 0
        state.test_output = ""
        state.regression_test = ""
        state.issue_text = f"[Sub-issue {next_idx + 1}/{len(sub_issues)}: {title}]\n{desc}".strip()
    return state


def checkpoint_node(state: AgentState) -> AgentState:
    """Save persistent session snapshot and progress ledger to disk."""
    state = coerce_state(state)
    status = "completed"
    if state.approved is False:
        status = "paused_human_review"
    elif test_failed(state):
        status = "paused_budget"

    save_session(state, status=status)
    return state


def _route_after_sandbox(state: AgentState) -> str:
    """Retry with new evidence while tests fail and budget remains, else review."""
    state = coerce_state(state)
    if state.escalation:
        return "approval"
    # AR-2: structured verdict wins; a PASSED output embedding traceback
    # text (warnings, full-suite echoes) must NOT route back to replan.
    failed = test_failed(state)
    if failed and state.retry_count < MAX_RETRIES:
        return "replan"
    return "critic"


def _route_after_confidence_gate(state: AgentState) -> str:
    """Escalate before patching when the planner's confidence is too low."""
    return "approval" if coerce_state(state).escalation else "regression_test"


def _route_after_approval(state: AgentState) -> str:
    """Pure router — no state mutations here (sub-issue advancement lives in approval_node)."""
    state = coerce_state(state)
    if state.approved is False:
        return "checkpoint"

    sub_issues = state.sub_issues
    if not isinstance(sub_issues, list):
        return "checkpoint"

    curr_idx = state.current_sub_issue_index if state.current_sub_issue_index is not None else 0
    if curr_idx + 1 < len(sub_issues):
        return "planner"
    return "checkpoint"


def build_graph():
    """Compile and return the single-agent ISHA state graph."""
    from src.agents.nodes import replan_node

    workflow = StateGraph(AgentState)

    workflow.add_node("investigation", investigation_node)
    workflow.add_node("decomposer", decomposer_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("confidence_gate", confidence_gate_node)
    workflow.add_node("regression_test", regression_test_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("candidates", candidate_node)
    workflow.add_node("sandbox", sandbox_node)
    workflow.add_node("replan", replan_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("approval", approval_node)
    workflow.add_node("checkpoint", checkpoint_node)

    workflow.set_entry_point("investigation")
    workflow.add_edge("investigation", "decomposer")
    workflow.add_edge("decomposer", "planner")
    workflow.add_edge("planner", "confidence_gate")
    workflow.add_conditional_edges(
        "confidence_gate",
        _route_after_confidence_gate,
        {"approval": "approval", "regression_test": "regression_test"},
    )
    workflow.add_edge("regression_test", "coder")
    workflow.add_edge("coder", "candidates")
    workflow.add_edge("candidates", "sandbox")
    workflow.add_conditional_edges(
        "sandbox",
        _route_after_sandbox,
        {"replan": "replan", "critic": "critic", "approval": "approval"},
    )
    workflow.add_edge("replan", "coder")
    workflow.add_edge("critic", "approval")
    workflow.add_conditional_edges(
        "approval",
        _route_after_approval,
        {"planner": "planner", "checkpoint": "checkpoint"},
    )
    workflow.add_edge("checkpoint", END)

    return workflow.compile(checkpointer=get_checkpointer())


compiled_graph = build_graph()


# ── Multi-agent graph (Phase 6) ──────────────────────────────────────────── #

def arbitration_fanin_node(state, config: RunnableConfig | None = None) -> dict:
    """Fan-in: score every branch's attempt and keep the LAYA winner.

    Named distinctly from src.review.arbitration.arbitration_node (the pure
    scorer used here as `arbitrate`) — same name, different signature was
    inviting cross-imports (AR-7)."""
    state = coerce_state(state)
    from src.review.arbitration import arbitration_node as arbitrate
    from src.review.arbitration import collect_attempts

    thread_id = (config or {}).get("configurable", {}).get("thread_id", "default")
    results = collect_attempts(thread_id)
    winner = arbitrate(results)
    if not winner:
        return {}

    updates = {
        key: winner[key]
        for key in (
            "patch",
            "test_output",
            "retry_count",
            "critic_verdict",
            "critic_score",
            "worktree",
            "strategy",
        )
        if key in winner
    }
    updates["laya_scores"] = {
        **winner.get("laya_scores", {}),
        **winner.get("arbitration", {}),
    }
    return updates


_MERGED: dict[tuple, float] = {}
_MERGED_TTL = 300  # seconds — entries expire after 5 minutes
_MERGED_LOCK = threading.Lock()


def _merge_key(state: AgentState, thread_id: str) -> tuple:
    """Scope a merge to one logical winner: same thread + same instance +
    same winning patch. Two fan-out paths delivering the same winner dedupe;
    a different instance or patch on a reused thread_id is a NEW merge."""
    import hashlib

    patch = state.patch or ""
    digest = hashlib.sha1(patch.encode("utf-8", "replace")).hexdigest()[:16]
    return (thread_id, state.instance_id or "", state.strategy or "", digest)


def _already_merged(thread_id: str, key: tuple | None = None) -> bool:
    """Return True if this exact merge already ran; register it if not.

    Lock-guarded: concurrent workers sharing a thread_id (e.g. the
    "default" fallback) can no longer double-merge past each other.
    """
    import time

    now = time.time()
    with _MERGED_LOCK:
        # Expire stale entries so re-runs in long-lived processes work.
        stale = [k for k, ts in _MERGED.items() if now - ts > _MERGED_TTL]
        for k in stale:
            del _MERGED[k]

        key = key or (thread_id,)
        if key in _MERGED:
            return True
        _MERGED[key] = now
        return False


def merger_node(state, config: RunnableConfig | None = None) -> AgentState:
    """Apply the winning patch to the real repo, then clean up worktrees."""
    state = coerce_state(state)
    from src.review.arbitration import collect_attempts
    from src.tools.patch_engine import apply_patch
    from src.tools.worktree_manager import cleanup_all_worktrees

    thread_id = (config or {}).get("configurable", {}).get("thread_id", "default")
    collect_attempts(thread_id)  # drain any leftovers

    # The merger can be reached by several arbitration fan-out paths;
    # only the first delivery of each logical winner does the real work.
    if _already_merged(thread_id, _merge_key(state, thread_id)):
        return state

    # P0.2 Execution-first hierarchy:
    # 1. Hard gates: repro passes, 0 regressions, static gate passes, secret scan clean.
    # 2. A critic "flagged" or "low_quality" verdict routes to human review, not to deletion/veto.
    # 3. Only security scanner findings are automatic vetoes.
    passed = test_passed(state)
    
    # Check guardrails (the ONLY automatic veto)
    is_blocked = False
    try:
        from src.guardrails.scanner import scan as _scan

        if state.patch and _scan(state.patch, state.issue_text).get("blocked"):
            state.approved = False
            state.escalation = "guardrail BLOCK: secrets/injection/destructive pattern"
            is_blocked = True
    except Exception:
        pass

    # Execution-first clearance: test-passing patches that pass security are cleared.
    # A critic non-approval sets approved=False to record review required, but doesn't discard.
    if passed and not is_blocked:
        cleared = True
        if state.approved is None:
            state.approved = True if state.critic_verdict == "approved" else False
    else:
        cleared = False

    apply = bool((config or {}).get("configurable", {}).get("apply", False))

    if apply and passed and cleared and state.patch:
        ok, message = apply_patch(state.repo_path, state.patch)
        print(f"\n  merger: {'applied' if ok else 'FAILED'} — {message}")
        from src.tools.git_manager import commit_fix

        if ok and (Path(state.repo_path) / ".git").exists():
            commit_fix(state.repo_path, f"ISHA: fix via {state.strategy} strategy")

    if state.repo_path:
        cleanup_all_worktrees(state.repo_path)

    # Save progress checkpoint
    status = "completed"
    if state.approved is False:
        status = "paused_human_review"
    save_session(state, status=status, note=f"Multi-agent winner: {state.strategy}")

    print(
        f"\n  merger: winner strategy={state.strategy} "
        f"score={state.critic_score:.3f} verdict={state.critic_verdict}"
    )
    return state


def build_multi_agent_graph():
    """Compile the fan-out/fan-in multi-agent ISHA graph."""
    from src.agents.attempt import attempt_node
    from src.agents.dispatch import STRATEGIES, dispatch_agents

    workflow = StateGraph(AgentState)

    workflow.add_node("investigation", investigation_node)
    workflow.add_node("decomposer", decomposer_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("confidence_gate", confidence_gate_node)
    workflow.add_node("regression_test", regression_test_node)
    workflow.add_node("arbitration", arbitration_fanin_node)
    workflow.add_node("approval", approval_node)
    workflow.add_node("merger", merger_node)
    workflow.add_node("checkpoint", checkpoint_node)

    # One isolated attempt chain per strategy (own worktree + retry budget).
    for i, _strategy in enumerate(STRATEGIES, start=1):
        workflow.add_node(f"attempt{i}", attempt_node)
        workflow.add_edge(f"attempt{i}", "arbitration")

    workflow.set_entry_point("investigation")
    workflow.add_edge("investigation", "decomposer")
    workflow.add_edge("decomposer", "planner")
    workflow.add_edge("planner", "confidence_gate")
    workflow.add_conditional_edges(
        "confidence_gate",
        _route_after_confidence_gate,
        {"approval": "approval", "regression_test": "regression_test"},
    )
    workflow.add_conditional_edges(
        "regression_test",
        dispatch_agents,
        [f"attempt{i}" for i in range(1, len(STRATEGIES) + 1)],
    )
    workflow.add_conditional_edges(
        "arbitration",
        lambda s: "approval" if s.critic_verdict == "flagged" else "merger",
        {"approval": "approval", "merger": "merger"},
    )
    workflow.add_edge("approval", "merger")
    workflow.add_edge("merger", "checkpoint")
    workflow.add_edge("checkpoint", END)

    return workflow.compile(checkpointer=get_checkpointer())


compiled_multi_graph = build_multi_agent_graph()


def run_issue(issue_text: str, repo_path: str | None = None, thread_id: str | None = None) -> AgentState:
    """Convenience wrapper: build state, invoke the graph, return the result."""
    from pathlib import Path

    from src.agents.context import build_repo_context
    from src.config import TARGET_REPO_PATH

    if thread_id is None:
        # Unique per invocation: reusing a thread_id across runs in one
        # process risks merger/ledger cross-talk (AR-3).
        import uuid

        thread_id = uuid.uuid4().hex[:8]

    repo_path = repo_path or TARGET_REPO_PATH
    if not Path(repo_path).is_dir():
        raise FileNotFoundError(
            f"Target repo not found: {repo_path} (set TARGET_REPO_PATH in .env or pass --repo)"
        )

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
