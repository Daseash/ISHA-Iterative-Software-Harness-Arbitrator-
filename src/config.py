"""
ISHA Configuration — Model routing, API setup, and Langfuse observability.

Routes planning through Gemini Flash (free tier) and patching through
Groq Llama with automatic fallback to Gemini.

Runtime modes:
  * live   — valid GOOGLE_API_KEY / GROQ_API_KEY in `.env`
  * offline — no keys, or a live call fails: the deterministic brain in
    `src.tools.offline_brain` answers so the pipeline never hard-fails.
"""

import logging
import os
import sys
import warnings

# Suppress internal background worker and third-party library warnings
warnings.filterwarnings("ignore")
logging.getLogger("LiteLLM").setLevel(logging.CRITICAL)
logging.getLogger("litellm").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
os.environ["LITELLM_LOG"] = "CRITICAL"

from dotenv import load_dotenv

load_dotenv()

# ── Agent Identity ──────────────────────────────────────────────────────────
AGENT_NAME = os.getenv("AGENT_NAME", "ISHA")

# ── Model routing (override via .env when providers rotate model ids) ──────
# Verified live: gemini-3.1-flash-lite answers while the flash tier is at 503,
# and Groq's llama-3.3-70b-versatile has been retired from the free tier.
PLANNER_MODEL = os.getenv("ISHA_PLANNER_MODEL", "gemini/gemini-3.1-flash-lite")
CODER_MODEL = os.getenv("ISHA_CODER_MODEL", "groq/qwen/qwen3.8-27b")
CODER_FALLBACKS = [
    m.strip()
    for m in os.getenv(
        "ISHA_CODER_FALLBACKS", "groq/allam-2-7b,gemini/gemini-3.1-flash-lite"
    ).split(",")
    if m.strip()
]
PLANNER_FALLBACKS = [
    m.strip()
    for m in os.getenv("ISHA_PLANNER_FALLBACKS", "groq/qwen/qwen3.8-27b").split(",")
    if m.strip()
]

# ── Model availability ─────────────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_ENABLED = bool(GOOGLE_API_KEY or GROQ_API_KEY)
OFFLINE_MODE = (not LLM_ENABLED) or os.getenv("ISHA_FORCE_OFFLINE", "0") == "1"

# ── LiteLLM Setup ──────────────────────────────────────────────────────────
try:
    import litellm

    litellm.suppress_debug_info = True
    litellm.set_verbose = False
    litellm.drop_params = True
    # Langfuse is traced explicitly from src/observability (Phase 9); the
    # litellm→langfuse callback bridge is version-sensitive and off by default.
    if os.getenv("ISHA_LITELLM_LANGFUSE", "0") == "1":
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


def _note(mode: str, role: str, error: Exception) -> None:
    print(
        f"[config] {role} live call failed ({type(error).__name__}); "
        f"falling back to {mode} brain",
        file=sys.stderr,
    )


def call_planner(prompt: str) -> str:
    """Call Gemini Flash for planning, falling back to the offline brain."""
    if OFFLINE_MODE or litellm is None:
        try:
            return _offline(prompt)
        except Exception as e:
            return f"[PLANNER ERROR] offline mode: {e}"

    try:
        resp = litellm.completion(
            model=PLANNER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            fallbacks=[{PLANNER_MODEL: PLANNER_FALLBACKS}],
        )
        content = resp.choices[0].message.content
        if not content or content.strip().startswith(("[PLANNER ERROR", "[REGRESSION", "[CODER ERROR")):
            raise ValueError("empty planner response")
        return content
    except Exception as e:
        _note("offline", "planner", e)
        try:
            return _offline(prompt)
        except Exception as offline_error:
            return f"[PLANNER ERROR] {e} / offline: {offline_error}"


def call_coder(prompt: str) -> str:
    """Call Groq Llama for fast patch generation, with Gemini fallback."""
    if OFFLINE_MODE or litellm is None:
        try:
            return _offline(prompt)
        except Exception as e:
            return f"[CODER ERROR] offline mode: {e}"

    try:
        resp = litellm.completion(
            model=CODER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            fallbacks=[{CODER_MODEL: CODER_FALLBACKS}],
        )
        content = resp.choices[0].message.content
        if not content or content.strip().startswith(("[CODER ERROR", "[PLANNER ERROR")):
            raise ValueError("empty coder response")
        return content
    except Exception as e:
        _note("offline", "coder", e)
        try:
            return _offline(prompt)
        except Exception as offline_error:
            return f"[CODER ERROR] {e} / offline: {offline_error}"


def call_with_timeout(model: str, prompt: str, timeout: int = 60) -> str:
    """Low-level helper used by the dashboard and eval harness."""
    if litellm is None:
        return _offline(prompt)
    resp = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        timeout=timeout,
    )
    return resp.choices[0].message.content or ""
