"""
ISHA Attempt Node — one full isolated fix attempt for a branch.

Runs coder → sandbox → self-correction loop → critic entirely inside a
single graph node so each parallel branch keeps its own worktree, strategy
and retry budget. Results fan in to arbitration through the attempt ledger.
"""

from langgraph.types import RunnableConfig

from src.agents.nodes import coder_node, sandbox_node
from src.agents.state import AgentState, coerce_state
from src.review.critic import critic_node

MAX_RETRIES = 3


def attempt_node(state, config: RunnableConfig | None = None) -> dict:
    """Execute one complete fix attempt and register it for arbitration."""
    branch: AgentState = coerce_state(state)

    for _ in range(MAX_RETRIES + 1):
        branch = coder_node(branch)
        branch = sandbox_node(branch)
        failed = "FAILED" in (branch.test_output or "")
        if not failed or branch.retry_count >= MAX_RETRIES:
            break

    branch = critic_node(branch, config)
    return branch.model_dump()
