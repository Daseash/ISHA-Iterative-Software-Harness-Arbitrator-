"""
ISHA Agent State — Pydantic model for the agentic loop state.

Every node in the LangGraph takes this state in and returns an updated copy.
LAYA scores, worktree paths, and strategy info are carried through the graph.

Every field carries a "last write wins" reducer so the multi-agent graph can
update the same keys concurrently from parallel branches without LangGraph
raising InvalidUpdateError.
"""

from typing import Annotated, Optional

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

    # ── Planning ────────────────────────────────────────────────────────────
    plan: Annotated[str, _last] = Field(default="", description="Structured fix plan from the planner")

    # ── Testing ─────────────────────────────────────────────────────────────
    regression_test: Annotated[str, _last] = Field(default="", description="Red/green regression test code")

    # ── Patching ────────────────────────────────────────────────────────────
    patch: Annotated[str, _last] = Field(default="", description="Unified diff patch from the coder")
    test_output: Annotated[str, _last] = Field(default="", description="Pytest stdout+stderr from sandbox")
    retry_count: Annotated[int, _last] = Field(default=0, description="Number of self-correction retries")

    # ── Review (LAYA-powered) ───────────────────────────────────────────────
    critic_verdict: Annotated[Optional[str], _last] = Field(default=None, description="approved | flagged | low_quality")
    critic_score: Annotated[float, _last] = Field(default=0.0, description="LAYA composite score (0-1)")
    approved: Annotated[Optional[bool], _last] = Field(default=None, description="Human approval status")

    # ── Multi-Agent ─────────────────────────────────────────────────────────
    worktree: Annotated[str, _last] = Field(default="", description="Isolated git worktree path for this attempt")
    strategy: Annotated[str, _last] = Field(default="default", description="Patching strategy for this attempt")

    # ── LAYA Decision Scores ────────────────────────────────────────────────
    laya_scores: Annotated[dict, _last] = Field(default_factory=dict, description="Detailed LAYA scoring breakdown")


def coerce_state(obj) -> AgentState:
    """Accept AgentState or a plain dict (LangGraph Send payloads) uniformly."""
    if isinstance(obj, AgentState):
        return obj
    if isinstance(obj, dict):
        return AgentState(**obj)
    return obj
