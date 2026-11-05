"""
ISHA Attempt Node — one full isolated fix attempt for a branch.

Runs coder → sandbox → self-correction loop → critic entirely inside a
single graph node so each parallel branch keeps its own worktree, strategy
and retry budget. Results fan in to arbitration through the attempt ledger.
"""

from langgraph.types import RunnableConfig

from src.agents.nodes import coder_node, sandbox_node
from src.agents.state import AgentState, coerce_state, test_failed
from src.review.critic import critic_node

import os

MAX_RETRIES = int(os.getenv("ISHA_MAX_RETRIES", "3"))


def attempt_node(state, config: RunnableConfig | None = None) -> dict:
    """Execute one complete fix attempt and register it for arbitration."""
    from src.agents.nodes import replan_node

    branch: AgentState = coerce_state(state)

    for _ in range(MAX_RETRIES + 1):
        branch = coder_node(branch)
        branch = sandbox_node(branch)
        # AR-2: structured verdict — PASSED output embedding FAILED text
        # must break the loop, never replan.
        failed = test_failed(branch)
        if failed:
            # P0-10: replan with fresh failure evidence (was never called).
            try:
                branch = replan_node(branch)
            except Exception:
                pass
        if not failed or branch.retry_count >= MAX_RETRIES:
            break

    branch = critic_node(branch, config)
    # P0-10: always record the attempt ledger (arbitration drained [] before).
    try:
        from src.review.arbitration import record_attempt

        thread_id = (config or {}).get("configurable", {}).get("thread_id", "default")
        record_attempt(thread_id, branch.model_dump())
    except Exception:
        pass
    return branch.model_dump()
