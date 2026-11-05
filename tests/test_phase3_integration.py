"""Add a small offline regression test for the Phase 3 integration.

Covers:
  * ISHASpecialistSuite repo mapping + offline guard (no heavy deps needed)
  * ISHA_MODE parsing and self-hosted chain rewrite
  * candidate tournament spec shape
"""
from __future__ import annotations

import importlib


def _reload(module, monkeypatch, **env):
    for k in ("ISHA_MODE", "ISHA_MODAL_VLLM_URL", "ISHA_ENDPOINT_KEY", "ISHA_FORCE_OFFLINE"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    return importlib.reload(module)


def test_specialist_suite_repo_ids():
    from src.models.specialist_onnx import ISHASpecialistSuite

    suite = ISHASpecialistSuite(hub_user="acme")
    assert suite.repo_id("loc") == "acme/isha-loc-reranker-v1-int8-onnx"
    assert suite.repo_id("redgate") == "acme/isha-redgate-v1-int8-onnx"
    assert suite.repo_id("laya") == "acme/isha-laya-verifier-v1-int8-onnx"


def test_specialist_rerank_empty_is_noop():
    from src.models.specialist_onnx import ISHASpecialistSuite

    suite = ISHASpecialistSuite()
    assert suite.rerank_files("issue", []) == []


def test_specialist_offline_guard(tmp_path, monkeypatch):
    from src.models import specialist_onnx

    monkeypatch.setenv("ISHA_FORCE_OFFLINE", "1")
    suite = specialist_onnx.ISHASpecialistSuite(cache_dir=str(tmp_path))
    try:
        suite._load("loc")
    except RuntimeError as exc:
        assert "ISHA_FORCE_OFFLINE=1" in str(exc)
    else:  # pragma: no cover - guard regression
        raise AssertionError("offline guard did not fire")


def test_config_mode_defaults_and_self_hosted(monkeypatch):
    import src.config as config

    _reload(config, monkeypatch)
    assert config.ISHA_MODE == "hybrid"

    _reload(
        config,
        monkeypatch,
        ISHA_MODE="self-hosted",
        ISHA_MODAL_VLLM_URL="https://example.test/v1",
        ISHA_ENDPOINT_KEY="secret",
    )
    assert config.PLANNER_CHAIN == ["openai/isha-coder-7b-dpo"]
    assert config.CODER_CHAIN == ["openai/isha-coder-7b-dpo"]
    assert config.REPRO_CHAIN == ["openai/isha-coder-7b-dpo"]

    # Restore defaults for the rest of the session.
    _reload(config, monkeypatch)


def test_candidate_tournament_spec():
    import src.gateway.model_router as router

    spec = router.CANDIDATE_TOURNAMENT_SPEC
    assert len(spec) == 4
    assert {c["temperature"] for c in spec} == {0.20}
    assert all(c["candidate_id"] for c in spec)
