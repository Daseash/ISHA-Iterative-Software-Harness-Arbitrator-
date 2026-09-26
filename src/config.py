"""
ISHA Configuration — Model routing, API setup, and Langfuse observability.

Routes planning through Gemini 2.5 Flash (free tier) and patching through
Groq Llama 3.3 70B with automatic fallback to Gemini.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ── Agent Identity ──────────────────────────────────────────────────────────
AGENT_NAME = os.getenv("AGENT_NAME", "ISHA")

# ── LiteLLM Setup ──────────────────────────────────────────────────────────
try:
    import litellm

    litellm.success_callback = ["langfuse"]
    litellm.failure_callback = ["langfuse"]
except ImportError:
    litellm = None


def call_planner(prompt: str) -> str:
    """Call Gemini 2.5 Flash for planning and deep reasoning tasks.

    Gemini's 1M+ token context handles full-repo ingestion and issue specs.
    """
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
