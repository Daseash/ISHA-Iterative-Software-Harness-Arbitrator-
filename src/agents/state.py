"""
ISHA Agent State — Pydantic model for the agentic loop state.

Every node in the LangGraph takes this state in and returns an updated copy.
LAYA scores, worktree paths, and strategy info are carried through the graph.
"""

from typing import Optional

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """Central state object passed through every node in the ISHA pipeline."""

    # ── Input ───────────────────────────────────────────────────────────────
    issue_text: str = Field(..., description="The bug report or issue description")
    repo_path: str = Field(default="", description="Path to the target repository")
    repo_context: str = Field(default="", description="AST map + RAG context for the repo")

    # ── Planning ────────────────────────────────────────────────────────────
    plan: str = Field(default="", description="Structured fix plan from the planner")

    # ── Testing ─────────────────────────────────────────────────────────────
    regression_test: str = Field(default="", description="Red/green regression test code")

    # ── Patching ────────────────────────────────────────────────────────────
    patch: str = Field(default="", description="Unified diff patch from the coder")
    test_output: str = Field(default="", description="Pytest stdout+stderr from sandbox")
    retry_count: int = Field(default=0, description="Number of self-correction retries")

    # ── Review (LAYA-powered) ───────────────────────────────────────────────
    critic_verdict: Optional[str] = Field(default=None, description="approved | flagged | low_quality")
    critic_score: float = Field(default=0.0, description="LAYA composite score (0-1)")
    approved: Optional[bool] = Field(default=None, description="Human approval status")

    # ── Multi-Agent ─────────────────────────────────────────────────────────
    worktree: str = Field(default="", description="Isolated git worktree path for this attempt")
    strategy: str = Field(default="default", description="Patching strategy for this attempt")

    # ── LAYA Decision Scores ────────────────────────────────────────────────
    laya_scores: dict = Field(default_factory=dict, description="Detailed LAYA scoring breakdown")
