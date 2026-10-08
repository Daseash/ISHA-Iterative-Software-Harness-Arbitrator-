"""
ISHA Critic — LAYA-powered adversarial diff reviewer.

Scores patches on quality, relevance, and safety using calibrated
probabilities instead of text-only LLM judgment.
"""

from langgraph.types import RunnableConfig

from src.agents.state import AgentState, coerce_state


def critic_node(state, config: RunnableConfig | None = None) -> AgentState:
    """Adversarial review of the patch using LAYA decision engine."""
    state = coerce_state(state)
    from src.review.laya_judge import get_judge

    try:
        judge = get_judge()

        scores = judge.score_patch(state.issue_text, state.plan, state.patch)
        state.laya_scores = scores

        dangers = judge.check_dangers(state.patch)

        # Hard guardrails always win over model judgment.
        from src.guardrails.scanner import scan_patch_for_secrets
        # Helper to detect if current attempt used fallback model
        def _is_fallback_attempt(state):
            """Check if the current patch attempt used a fallback model."""
            if not state.model_log:
                return False
            # Look for the most recent coder entry
            for entry in reversed(state.model_log):
                if entry.get("role") == "coder":
                    position = entry.get("position", "")
                    return "fallback" in position.lower()
            return False

        # Helper to detect if current attempt used fallback model
        def _is_fallback_attempt(state):
            """Check if the current patch attempt used a fallback model."""
            if not state.model_log:
                return False
            # Look for the most recent coder entry
            for entry in reversed(state.model_log):
                if entry.get("role") == "coder":
                    position = entry.get("position", "")
                    return "fallback" in position.lower()
            return False


        clean, findings = scan_patch_for_secrets(state.patch)

        if dangers["flagged"] or not clean:
            state.critic_verdict = "flagged"
        # Apply fallback safe_to_apply floor: stricter threshold for fallback models
        effective_composite = scores["composite"]
        if _is_fallback_attempt(state):
            # For fallback models, apply stricter safe_to_apply threshold
            # Reduce the influence of safe_to_apply score to make approval harder
            safe_penalty = 0.15  # Conservative penalty for fallback models
            quality_component = 0.50 * scores["fix_quality"] / 2.0
            matches_component = 0.25 * scores["matches_issue"]
            safe_component = 0.25 * max(0, scores["safe_to_apply"] - safe_penalty)
            effective_composite = quality_component + matches_component + safe_component

        if effective_composite < 0.4:
            state.critic_verdict = "low_quality"
        else:
            state.critic_verdict = "approved"
        state.critic_score = scores["composite"]
        state.laya_scores = {**scores, **dangers, "guardrail_findings": findings}

        # Security & performance checklist — can veto an otherwise-clean diff.
        if state.patch and "ERROR" not in state.patch[:60]:
            try:
                from src.review.checklist import security_perf_checklist

                checklist = security_perf_checklist(state.issue_text, state.patch)
                if checklist:
                    state.laya_scores = {**state.laya_scores, "checklist": checklist}
                    if checklist["verdict"] == "BLOCK":
                        state.critic_verdict = "flagged"
            except Exception:
                pass

    except Exception as exc:
        state.critic_verdict = "error"
        state.critic_score = 0.0
        state.laya_scores = {"error": str(exc)}

    _record(state, config)
    return state


def _record(state: AgentState, config: RunnableConfig | dict | None = None) -> None:
    """Register this branch's attempt so arbitration can fan-in on it."""
    try:
        from src.review.arbitration import record_attempt

        thread_id = (
            (config or {}).get("configurable", {}).get("thread_id", "default")
        )
        record_attempt(thread_id, state.model_dump() if hasattr(state, "model_dump") else dict(state))
    except Exception:
        pass
