"""Unified model router for ISHA (Subsystem 11).

Routes Node 3 (planner), Node 5a (regression test) and the Node 6/8 candidate
tournament across cloud providers and the self-hosted ISHA-Coder-7B-DPO
serverless endpoint.

Runtime mode comes from ``ISHA_MODE``:

- ``hybrid`` (default): trained specialists plus cloud LLM fallbacks.
- ``self-hosted``: every alias resolves to the Modal vLLM endpoint.
- ``cloud``: original cloud-only behaviour (backward compatible).

Note: routers describe *what to call*.  The LangGraph fan-out must still cap
in-flight candidate workers (``MAX_IN_FLIGHT_CANDIDATES``) because free-tier
Groq TPM throttles a four-way burst.
"""

from __future__ import annotations

import os

DEFAULT_MODAL_URL = (
    "https://daseash--isha-coder-7b-serverless-serve-vllm.modal.run/v1"
)

ISHA_MODE = os.getenv("ISHA_MODE", "hybrid").strip().lower()
if ISHA_MODE not in {"hybrid", "self-hosted", "cloud"}:
    ISHA_MODE = "hybrid"

MAX_IN_FLIGHT_CANDIDATES = 2

_TOKEN_ENDPOINT = {
    "model": "openai/isha-coder-7b-dpo",
    "api_base": os.getenv("ISHA_MODAL_VLLM_URL", DEFAULT_MODAL_URL),
    "api_key": os.getenv("ISHA_ENDPOINT_KEY", "isha-serverless-token"),
}

CLOUD_MODELS = [
    # Node 3: Planner
    {"model_name": "node-planner", "litellm_params": {"model": "gemini/gemini-3.8-flash", "api_key": os.getenv("GEMINI_API_KEY")}},
    {"model_name": "node-planner-fb1", "litellm_params": {"model": "groq/openai/gpt-oss-120b", "api_key": os.getenv("GROQ_API_KEY")}},
    {"model_name": "node-planner-fb2", "litellm_params": {"model": "gemini/gemini-3.5-flash", "api_key": os.getenv("GEMINI_API_KEY")}},
    # Node 5a: Regression test
    {"model_name": "node-repro", "litellm_params": {"model": "groq/openai/gpt-oss-120b", "api_key": os.getenv("GROQ_API_KEY"), "reasoning_effort": "high"}},
    {"model_name": "node-repro-fb1", "litellm_params": {"model": "gemini/gemini-3.8-flash", "api_key": os.getenv("GEMINI_API_KEY")}},
    # Node 6/8: candidate tournament (constant temp=0.20 at call time)
    {"model_name": "cand-qwen38", "litellm_params": {"model": "groq/qwen/qwen3.8-27b", "api_key": os.getenv("GROQ_API_KEY"), "rpm": 20, "tpm": 160000}},
    {"model_name": "cand-gpt-oss", "litellm_params": {"model": "groq/openai/gpt-oss-120b", "api_key": os.getenv("GROQ_API_KEY"), "rpm": 20, "tpm": 120000}},
    {"model_name": "cand-gemini38", "litellm_params": {"model": "gemini/gemini-3.8-flash", "api_key": os.getenv("GEMINI_API_KEY"), "rpm": 10}},
]

SELF_HOSTED_MODELS = [
    {"model_name": name, "litellm_params": dict(_TOKEN_ENDPOINT)}
    for name in (
        "node-planner",
        "node-planner-fb1",
        "node-planner-fb2",
        "node-repro",
        "node-repro-fb1",
        "cand-isha-dpo",
        "cand-qwen38",
        "cand-gpt-oss",
        "cand-gemini38",
    )
]


def candidate_tournament_spec() -> list[dict]:
    """Return the tournament matrix appropriate for the active mode."""
    spec = [
        {"candidate_id": "candidate-1", "model_group": "cand-qwen38", "strategy": "minimal_diff", "temperature": 0.20},
        {"candidate_id": "candidate-2", "model_group": "cand-gpt-oss", "strategy": "root_cause_first", "temperature": 0.20},
        {"candidate_id": "candidate-3", "model_group": "cand-gemini38", "strategy": "call_site_aware", "temperature": 0.20},
        {"candidate_id": "candidate-4", "model_group": "cand-isha-dpo", "strategy": "invariant_hardened", "temperature": 0.20},
    ]
    if ISHA_MODE == "cloud":
        # No self-hosted endpoint: candidate-4 uses the next cloud model so the
        # tournament still has four slots.
        spec[3]["model_group"] = "cand-gemini38"
    return spec


CANDIDATE_TOURNAMENT_SPEC = candidate_tournament_spec()


def build_isha_router():
    """Build the LiteLLM router for the active ISHA_MODE."""
    from litellm import Router

    if ISHA_MODE == "self-hosted":
        model_list = SELF_HOSTED_MODELS
        fallbacks = [
            {"node-planner": ["node-planner-fb1", "node-planner-fb2"]},
            {"node-repro": ["node-repro-fb1"]},
            {"cand-qwen38": ["cand-isha-dpo"]},
            {"cand-gpt-oss": ["cand-isha-dpo"]},
            {"cand-gemini38": ["cand-isha-dpo"]},
        ]
    else:
        model_list = list(CLOUD_MODELS)
        if ISHA_MODE == "hybrid":
            model_list.append({"model_name": "cand-isha-dpo", "litellm_params": dict(_TOKEN_ENDPOINT)})
            fallbacks = [
                {"node-planner": ["node-planner-fb1", "node-planner-fb2"]},
                {"node-repro": ["node-repro-fb1"]},
                {"cand-qwen38": ["cand-gemini38"]},
                {"cand-gpt-oss": ["cand-qwen38"]},
                {"cand-gemini38": ["cand-isha-dpo"]},
                {"cand-isha-dpo": ["cand-qwen38"]},
            ]
        else:  # cloud
            fallbacks = [
                {"node-planner": ["node-planner-fb1", "node-planner-fb2"]},
                {"node-repro": ["node-repro-fb1"]},
                {"cand-qwen38": ["cand-gemini38"]},
                {"cand-gpt-oss": ["cand-qwen38"]},
                {"cand-gemini38": ["cand-qwen38"]},
            ]

    return Router(
        model_list=model_list,
        cooldown_time=300,
        num_retries=2,
        fallbacks=fallbacks,
    )
