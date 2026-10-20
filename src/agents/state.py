"""
ISHA Agent State — Pydantic model for the agentic loop state.

Every node in the LangGraph takes this state in and returns an updated copy.
LAYA scores, worktree paths, and strategy info are carried through the graph.

Scalar / dict fields carry a "last write wins" reducer. Append-only list
fields (localization, context_notes, candidates, consistency_warnings,
model_log) carry an additive reducer so parallel Send() branches concatenate
instead of dropping all but the last writer (P0-04 / AR-1).
"""

from typing import Annotated, Optional

import operator

from pydantic import BaseModel, Field


def _last(a, b):
    """Reducer: concurrent writers resolve to the most recent value."""
    return b


class AgentState(BaseModel):
    """Central state object passed through every node in the ISHA pipeline."""

    # ── Input ───────────────────────────────────────────────────────────────
    issue_text: Annotated[str, _last] = Field(..., description="The bug report or issue description")
    repo_path: Annotated[str, _last] = Field(default="", description="Path to the target repository")
    repo_context: Annotated[str, _last] = Field(default="", description="AST map + RAG context for the repo")

    # ── Investigation ───────────────────────────────────────────────────────
    investigation_report: Annotated[str, _last] = Field(default="", description="Diagnostic report from pre-planning investigation")

    # ── Localization (Phase 2) ─────────────────────────────────────────────
    localization: Annotated[list, operator.add] = Field(default_factory=list, description="Ranked file/symbol/line candidates for the bug")
    context_notes: Annotated[list, operator.add] = Field(default_factory=list, description="Structured notes from gates/verification for the coder")

    # ── Hierarchical Decomposition ──────────────────────────────────────────
    sub_issues: Annotated[list, _last] = Field(default_factory=list, description="Decomposed list of atomic sub-issues")
    current_sub_issue_index: Annotated[int, _last] = Field(default=0, description="Active sub-issue index")

    # ── Planning ────────────────────────────────────────────────────────────
    plan: Annotated[str, _last] = Field(default="", description="Structured fix plan from the planner")
    planner_confidence: Annotated[float, _last] = Field(default=-1.0, description="Planner self-reported confidence 0-1; -1 = unknown")
    blast_radius: Annotated[dict, _last] = Field(default_factory=dict, description="Caller fan-out / blast radius of the symbols under change")
    escalation: Annotated[str, _last] = Field(default="", description="Reason this run was routed to human escalation instead of patching")

    # ── Testing & Baseline Gate ─────────────────────────────────────────────
    regression_test: Annotated[str, _last] = Field(default="", description="Red/green regression test code")
    repro_ok: Annotated[Optional[bool], _last] = Field(default=None, description="True if generated repro test produced a genuine failing assertion without collection errors")
    repro_valid: Annotated[Optional[bool], _last] = Field(default=None, description="True if repro test is a verified failing RED on unpatched code")
    repro_output: Annotated[str, _last] = Field(default="", description="Output of baseline repro test run")
    baseline_repro_failed: Annotated[Optional[bool], _last] = Field(default=None, description="True if generated repro test failed (RED) on unmodified baseline repo")
    baseline_repro_output: Annotated[str, _last] = Field(default="", description="Output of repro test execution on unmodified baseline repo")
    failure_classification: Annotated[str, _last] = Field(default="", description="Classified failure mode for evidence-based re-planning")
    local_sandbox_status: Annotated[str, _last] = Field(default="not_run", description="passed | failed | no_fix | infra | not_run (local sandbox execution; set by sandbox_node)")
    official_docker_status: Annotated[str, _last] = Field(default="not_run", description="passed | failed | not_run (official Docker container execution)")

    # ── Patching ────────────────────────────────────────────────────────────
    patch: Annotated[str, _last] = Field(default="", description="Unified diff patch from the coder")
    instance_id: Annotated[str, _last] = Field(default="", description="SWE-bench instance id (benchmark runs only)")

    # ── Candidates (Phase 4/5/6) ────────────────────────────────────────────
    candidates: Annotated[list, operator.add] = Field(default_factory=list, description="All gated candidates for this issue, with gate/verify/LAYA evidence")
    selected_candidate: Annotated[dict, _last] = Field(default_factory=dict, description="Why this candidate won: tier, score, verification")
    test_output: Annotated[str, _last] = Field(default="", description="Pytest stdout+stderr from sandbox")
    full_test_output: Annotated[str, _last] = Field(default="", description="Full repo test suite output to catch collateral regressions")
    retry_count: Annotated[int, _last] = Field(default=0, description="Number of self-correction retries")
    consistency_warnings: Annotated[list, operator.add] = Field(default_factory=list, description="Cross-file signature & call-site warnings")

    # ── Review (LAYA-powered) ───────────────────────────────────────────────
    critic_verdict: Annotated[Optional[str], _last] = Field(default=None, description="approved | flagged | low_quality")
    critic_score: Annotated[float, _last] = Field(default=0.0, description="LAYA composite score (0-1)")
    approved: Annotated[Optional[bool], _last] = Field(default=None, description="Human approval status")

    # ── Multi-Agent & Session ───────────────────────────────────────────────
    worktree: Annotated[str, _last] = Field(default="", description="Isolated git worktree path for this attempt")
    strategy: Annotated[str, _last] = Field(default="default", description="Patching strategy for this attempt")
    session_id: Annotated[str, _last] = Field(default="", description="Persistent session ID for checkpointing and resumption")

    # ── LAYA Decision Scores ────────────────────────────────────────────────
    laya_scores: Annotated[dict, _last] = Field(default_factory=dict, description="Detailed LAYA scoring breakdown")

    # ── Model Usage Audit Log ───────────────────────────────────────────────
    model_log: Annotated[list, operator.add] = Field(default_factory=list, description="Which model handled each pipeline step (role, model, position)")
    model_name: Annotated[str, _last] = Field(default="", description="Coder model id for the winning patch")


def coerce_state(obj) -> AgentState:
    """Accept AgentState or a plain dict (LangGraph Send payloads) uniformly."""
    if isinstance(obj, AgentState):
        return obj
    if isinstance(obj, dict):
        return AgentState(**obj)
    raise TypeError(f"coerce_state: expected AgentState or dict, got {type(obj).__name__}")


# ── Structured test verdict (AR-2) ──────────────────────────────────────────
# Routers switch on local_sandbox_status, never on substrings of test_output:
# a PASSED verdict can embed traceback text (warnings, xfail, full-suite
# echoes) and pytest's "0 failed" line must not read as FAILED. The substring
# fallback exists ONLY for states produced before the writer ran
# (status == "not_run") or non-terminal outcomes — it never overrides a known
# passed/failed status.

def test_failed(state) -> bool:
    """True when the sandbox verdict is failed. Status wins over substrings."""
    status = getattr(state, "local_sandbox_status", "not_run") or "not_run"
    if status == "failed":
        return True
    if status == "passed":
        return False
    return "FAILED" in (getattr(state, "test_output", "") or "")


def test_passed(state) -> bool:
    """True when the sandbox verdict is passed. Status wins over substrings."""
    status = getattr(state, "local_sandbox_status", "not_run") or "not_run"
    if status == "passed":
        return True
    if status == "failed":
        return False
    return "PASSED" in (getattr(state, "test_output", "") or "")
