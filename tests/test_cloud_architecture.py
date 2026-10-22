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
    assert models["minimal_diff"] == "mistral/codestral-latest"
    assert models["call_site_aware"] == "gemini/gemini-3.8-flash"
    assert models["root_cause_first"] == "groq/openai/gpt-oss-120b"
    assert models["defensive_fix"] == "mistral/codestral-latest"
    assert models["cross_file_audit"] == "gemini/gemini-3.8-flash"


def test_repro_chain_configuration():
    """Verify regression test chain defaults to deep reasoning models."""
    assert REPRO_MODEL == "groq/deepseek-r1-distill-llama-70b"
    assert "groq/openai/gpt-oss-120b" in REPRO_CHAIN or "gemini/gemini-3.8-flash" in REPRO_CHAIN


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
