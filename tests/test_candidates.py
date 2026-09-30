"""Tests for Phase 4 multi-model candidate generation and arbitration."""

from unittest.mock import MagicMock, patch

from src.agents.candidates import (
    Candidate,
    DEFAULT_STRATEGY_MODELS,
    generate_candidates,
    strategy_models,
)
from src.agents.state import AgentState
from src.config import CANDIDATE_1_MODEL, CANDIDATE_2_MODEL, CANDIDATE_3_MODEL


def test_strategy_models_has_three_distinct_models():
    """Verify that default candidate strategies route to 3 distinct model architectures."""
    models = strategy_models()
    assert models["minimal_diff"] == CANDIDATE_1_MODEL
    assert models["call_site_aware"] == CANDIDATE_2_MODEL
    assert models["root_cause_first"] == CANDIDATE_3_MODEL

    # The 3 core candidate models must not all be identical
    unique_models = {
        models["minimal_diff"],
        models["call_site_aware"],
        models["root_cause_first"],
    }
    assert len(unique_models) == 3, f"Expected 3 distinct models, got {unique_models}"


def test_candidate_as_dict_includes_model():
    """Verify Candidate.as_dict() serializes model information for arbitration audit."""
    cand = Candidate(
        index=1,
        strategy="minimal_diff",
        temperature=0.15,
        model="groq/qwen/qwen3.8-27b",
        patch="diff --git a/x.py b/x.py\n",
    )
    d = cand.as_dict()
    assert d["model"] == "groq/qwen/qwen3.8-27b"
    assert d["index"] == 1
    assert d["strategy"] == "minimal_diff"


def test_seed_patch_adopted_by_candidate_1_only():
    """Verify candidate 1 adopts seed_patch, while candidate 2 generates a fresh patch from its model."""
    state = AgentState(
        issue_text="fix a bug",
        repo_path="tests/dummy_repo",
        patch="--- a/x.py\n+++ b/x.py\n",
    )

    with (
        patch("src.agents.candidates._make_worktree", return_value="tests/dummy_repo"),
        patch("src.agents.candidates._apply", return_value=(True, "applied cleanly")),
        patch("src.agents.candidates.compile_gate", return_value=MagicMock(ok=True, errors=[])),
        patch("src.config.call_coder", return_value="```diff\n--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-old\n+new\n```"),
    ):
        cands = generate_candidates(state, n=2, seed_patch="seed_patch_diff")
        assert len(cands) == 2
        # Candidate 1 adopts the seed patch
        assert cands[0].patch == "seed_patch_diff"
        assert cands[0].strategy == "coder_default"
        # Candidate 2 receives a fresh patch and its assigned model
        assert cands[1].strategy == "call_site_aware"
        assert cands[1].model == CANDIDATE_2_MODEL


def test_candidate_model_env_override(monkeypatch):
    """ISHA_CANDIDATE_MODELS re-routes a strategy without a code change."""
    monkeypatch.setenv(
        "ISHA_CANDIDATE_MODELS", "minimal_diff=acme/one,call_site_aware=acme/two"
    )
    models = strategy_models()
    assert models["minimal_diff"] == "acme/one"
    assert models["call_site_aware"] == "acme/two"

    monkeypatch.delenv("ISHA_CANDIDATE_MODELS")
    assert strategy_models()["minimal_diff"] == CANDIDATE_1_MODEL


def test_model_log_entries_are_thread_tagged():
    """Parallel candidates must be able to tell their own answers apart."""
    import threading

    from src.config import _log_model, clear_model_log, get_model_log

    clear_model_log()
    _log_model("coder", "groq/qwen/qwen3.8-27b", "primary")
    entry = get_model_log()[-1]
    assert entry["thread"] == threading.current_thread().name
    clear_model_log()
