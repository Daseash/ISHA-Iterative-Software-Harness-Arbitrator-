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

        dangers = judge.check_dangers(state.patch)
        secrets = float(dangers.get("secrets_or_danger", 0.0) or 0.0)
        drift = float(dangers.get("logic_drift", 0.0) or 0.0)

        # Hard guardrails always win over model judgment.
        from src.guardrails.scanner import scan_patch_for_secrets

        # Co-equal tournament peers: Qwen3.8-27B, gpt-oss-120b, and gemini-3.8-flash
        # compete fairly on patch merit without fallback penalty bias.
        tier_penalty = 0.00
        scores = judge.score_patch(
            state.issue_text,
            state.plan,
            state.patch,
            secrets_or_danger=secrets,
            logic_drift=drift,
            tier_penalty=tier_penalty,
        )
        state.laya_scores = scores

        clean, findings = scan_patch_for_secrets(state.patch)
        effective_composite = scores["composite"]

        # Phase-0: per-org critic threshold (opt-in ISHA_CRITIC_PER_ORG=1).
        # Default stays the global 0.4 gate so running lanes keep semantics.
        threshold = 0.4
        try:
            from src.memory.store import org_critic_threshold

            org_thr = org_critic_threshold(
                getattr(state, "instance_id", "") or "", state.repo_path or ""
            )
            if org_thr is not None:
                threshold = org_thr
        except Exception:
            pass

        if dangers["flagged"] or not clean or effective_composite <= 0.0:
            state.critic_verdict = "flagged"
        elif effective_composite < threshold:
            state.critic_verdict = "low_quality"
        else:
            state.critic_verdict = "approved"
        state.critic_score = effective_composite
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
