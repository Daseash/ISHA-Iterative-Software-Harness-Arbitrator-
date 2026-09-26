"""
ISHA Configuration — Model routing, API setup, and Langfuse observability.

Routes planning through Gemini 2.5 Flash (free tier) and patching through
Groq Llama 3.3 70B with automatic fallback to Gemini.

When no API keys are configured the deterministic offline brain
(`src.tools.offline_brain`) answers instead, so the whole pipeline keeps
running in demo/CI mode. Add keys to `.env` to switch to live models.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ── Agent Identity ──────────────────────────────────────────────────────────
AGENT_NAME = os.getenv("AGENT_NAME", "ISHA")

# ── Model availability ─────────────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_ENABLED = bool(GOOGLE_API_KEY or GROQ_API_KEY)
OFFLINE_MODE = not LLM_ENABLED

# ── LiteLLM Setup ──────────────────────────────────────────────────────────
try:
    import litellm

    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]
except ImportError:
    litellm = None


def _offline(prompt: str) -> str:
    """Dispatch a prompt to the deterministic offline brain."""
    from src.tools import offline_brain

    if "pytest test that" in prompt or "REPRODUCES the bug" in prompt:
        return offline_brain.offline_regressor(prompt)
    if "unified diff patch" in prompt or "ONLY the diff" in prompt:
        return offline_brain.offline_coder(prompt)
    return offline_brain.offline_planner(prompt)


def call_planner(prompt: str) -> str:
    """Call Gemini 2.5 Flash for planning and deep reasoning tasks.

    Gemini's 1M+ token context handles full-repo ingestion and issue specs.
    """
    if OFFLINE_MODE:
        try:
            return _offline(prompt)
        except Exception as e:
            return f"[PLANNER ERROR] offline mode: {e}"

    if litellm is None:
        return "[ERROR] litellm not installed — cannot call planner."

    try:
        resp = litellm.completion(
            model="gemini/gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"[PLANNER ERROR] {e}"


def call_coder(prompt: str) -> str:
    """Call Groq Llama 3.3 70B for fast code patch generation.

    Falls back to Gemini Flash on rate limits. Groq's speed (~300-500 tok/s)
    keeps the test-fail-retry loop responsive.
    """
    if OFFLINE_MODE:
        try:
            return offline_coder_safe(prompt)
        except Exception as e:
            return f"[CODER ERROR] offline mode: {e}"

    if litellm is None:
        return "[ERROR] litellm not installed — cannot call coder."

    try:
        resp = litellm.completion(
            model="groq/llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            fallbacks=["gemini/gemini-2.5-flash"],
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"[CODER ERROR] {e}"


def offline_coder_safe(prompt: str) -> str:
    """Route coder prompts to the offline diff generator."""
    from src.tools import offline_brain

    return offline_brain.offline_coder(prompt)
