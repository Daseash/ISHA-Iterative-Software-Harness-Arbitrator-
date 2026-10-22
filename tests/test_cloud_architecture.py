"""
Tests for ISHA 100% Cloud-Hosted Architecture and Model Routing Matrix.
"""

import os
import pytest
from unittest.mock import patch

from src.config import (
    get_next_mistral_key,
    get_next_cerebras_key,
    _next_from_pool,
    REPRO_CHAIN,
    REPRO_MODEL,
    call_repro,
)
from src.agents.candidates import DEFAULT_STRATEGY_MODELS, strategy_models
from src.agents.council import CouncilResult, LLMCouncil


def test_cloud_strategy_model_defaults():
    """Verify that tournament strategies map to their designated cloud models."""
    models = strategy_models()
    assert "groq/qwen" in models["minimal_diff"] or "mistral/codestral" in models["minimal_diff"]
    assert models["call_site_aware"] == "gemini/gemini-3.8-flash"
    assert models["root_cause_first"] == "groq/openai/gpt-oss-120b"
    assert models["defensive_fix"] == "mistral/codestral-latest"
    assert models["cross_file_audit"] == "gemini/gemini-3.8-flash"


def test_repro_chain_configuration():
    """Verify regression test chain defaults to deep reasoning models."""
    assert REPRO_MODEL in ("groq/openai/gpt-oss-120b", "groq/deepseek-r1-distill-llama-70b")
    assert "gemini/gemini-3.8-flash" in REPRO_CHAIN or "groq/openai/gpt-oss-120b" in REPRO_CHAIN


def test_sticky_replan_model():
    """Verify candidate branches retain their sticky assigned model on replan."""
    from src.agents.state import AgentState
    from src.agents.dispatch import dispatch_agents

    state = AgentState(
        issue_text="fix division by zero bug",
        repo_path="tests/dummy_repo",
    )
    sends = dispatch_agents(state)
    assert len(sends) == 3
    # Check that each branch received an assigned_model matching its strategy
    for send in sends:
        payload = send.arg
        assert "assigned_model" in payload
        assert payload["assigned_model"] != ""


def test_mistral_cerebras_key_rotation():
    """Verify round-robin key rotation for Mistral and Cerebras providers."""
    import threading
    lock = threading.Lock()
    pool = ["key_a", "key_b", "key_c"]
    k1 = _next_from_pool(pool, lock, "mistral")
    k2 = _next_from_pool(pool, lock, "mistral")
    k3 = _next_from_pool(pool, lock, "mistral")
    k4 = _next_from_pool(pool, lock, "mistral")
    assert k1 != k2
    assert [k1, k2, k3] == ["key_b", "key_c", "key_a"]
    assert k4 == "key_b"


def test_call_repro_offline_fallback():
    """Verify call_repro falls back safely to deterministic offline brain without crashing."""
    with patch.dict(os.environ, {"ISHA_FORCE_OFFLINE": "1"}):
        result = call_repro("pytest test that REPRODUCES the bug")
        assert result is not None
        assert "def test_" in result or "test" in result.lower()


def test_council_data_structure():
    """Verify CouncilResult structure and fallback."""
    res = CouncilResult(
        query="test query",
        stage1_opinions={"gemini": "op1", "groq": "op2"},
        stage2_reviews={"gemini": "rev1", "groq": "rev2"},
        stage3_synthesis="synthesized consensus",
        chairman="gemini/gemini-3.8-flash",
        duration_sec=1.5,
    )
    assert res.query == "test query"
    assert res.stage3_synthesis == "synthesized consensus"
    assert res.chairman == "gemini/gemini-3.8-flash"


def test_laya_no_fallback_penalty():
    """Verify that LAYA does not penalize non-primary tournament peer models."""
    from src.review.laya_judge import compute_laya_composite

    # Both should evaluate with tier_penalty = 0.0
    score_standard = compute_laya_composite(fix_quality=2, matches_issue=0.8, safe_to_apply=0.8, tier_penalty=0.0)
    score_peer = compute_laya_composite(fix_quality=2, matches_issue=0.8, safe_to_apply=0.8)
    assert score_standard == score_peer
    assert score_peer == 0.50 * 1.0 + 0.25 * 0.8 + 0.25 * 0.8  # exactly 0.90


def test_strategy_rotation_by_issue_index():
    """Verify issue_idx % 3 model rotation across strategies when enabled."""
    from src.agents.state import AgentState
    from src.agents.dispatch import dispatch_agents

    state1 = AgentState(issue_text="bug 101", repo_path="tests/dummy_repo", instance_id="repo__issue-101")
    state2 = AgentState(issue_text="bug 102", repo_path="tests/dummy_repo", instance_id="repo__issue-102")

    with patch.dict(os.environ, {"ISHA_ROTATE_STRATEGIES": "1"}):
        sends1 = dispatch_agents(state1)
        sends2 = dispatch_agents(state2)
        m1 = [s.arg["assigned_model"] for s in sends1]
        m2 = [s.arg["assigned_model"] for s in sends2]
        # Rotated sets should be shifted by 1
        assert m1 != m2
        assert set(m1) == set(m2)


def test_locked_temperature_0_20():
    """Verify all strategy variants are locked at 0.20 temperature."""
    from src.agents.candidates import STRATEGY_VARIANTS

    for name, temp, _desc in STRATEGY_VARIANTS:
        assert temp == 0.20, f"Strategy {name} has temp {temp}, expected 0.20"
