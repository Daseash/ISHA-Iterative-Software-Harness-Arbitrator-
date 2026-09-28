"""
ISHA Configuration — Model routing with fallback chains, API setup, and observability.

Each role (planner, coder) has an ordered chain of models.  On each call,
the chain is tried in order: the first model that returns a valid response
wins.  Every attempt is logged transparently so the output always shows
which model actually produced the result.

Runtime modes:
  * live   — valid GOOGLE_API_KEY / GROQ_API_KEY in `.env`
  * offline — no keys, or all chain models fail: the deterministic brain in
    `src.tools.offline_brain` answers so the pipeline never hard-fails.
"""

import logging
import os
import re
import sys
import time
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

# Target repository — point at any real checkout via .env / environment.
# Every consumer (parser, indexer, sandbox, git manager) already takes the
# path as an argument; this is the single default they share.
TARGET_REPO_PATH = os.getenv("TARGET_REPO_PATH", "tests/dummy_repo")


# ── Model Fallback Chains ──────────────────────────────────────────────────
# Each role has an ordered list: primary → fallback1 → fallback2 → ...
# The first model that answers successfully wins.

def _parse_chain(primary_env: str, primary_default: str,
                 fallbacks_env: str, fallbacks_default: str) -> list:
    """Build an ordered model chain from env vars."""
    primary = os.getenv(primary_env, primary_default)
    fallbacks = [
        m.strip() for m in
        os.getenv(fallbacks_env, fallbacks_default).split(",")
        if m.strip()
    ]
    return [primary] + fallbacks


PLANNER_CHAIN = _parse_chain(
    "ISHA_PLANNER_MODEL", "groq/qwen/qwen3.8-27b",
    "ISHA_PLANNER_FALLBACKS",
    "groq/openai/gpt-oss-120b,groq/openai/gpt-oss-20b,"
    "gemini/gemini-3.8-flash,gemini/gemini-3.5-flash,gemini/gemini-3.1-flash-lite",
)

CODER_CHAIN = _parse_chain(
    "ISHA_CODER_MODEL", "groq/qwen/qwen3.8-27b",
    "ISHA_CODER_FALLBACKS",
    "groq/openai/gpt-oss-120b,groq/openai/gpt-oss-20b,"
    "gemini/gemini-3.8-flash,gemini/gemini-3.5-flash,gemini/gemini-3.1-flash-lite",
)

# Backward-compatible aliases
PLANNER_MODEL = PLANNER_CHAIN[0]
CODER_MODEL = CODER_CHAIN[0]
PLANNER_FALLBACKS = PLANNER_CHAIN[1:]
CODER_FALLBACKS = CODER_CHAIN[1:]


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


# ── Transparent Model Usage Log ────────────────────────────────────────────
# Every call records which model actually answered so results are auditable.

_model_log: list = []


def get_model_log() -> list:
    """Return the ordered list of model-usage entries."""
    return list(_model_log)


def clear_model_log() -> None:
    """Reset the model log for a new run."""
    _model_log.clear()


def _short_name(model: str) -> str:
    """Extract the readable model name: 'gemini/gemini-3.8-flash' → 'gemini-3.8-flash'."""
    return model.rsplit("/", 1)[-1] if "/" in model else model


def _log_model(role: str, model: str, position: str, note: str = "") -> None:
    """Record that a model was used for a role."""
    entry = {
        "role": role,
        "model": _short_name(model),
        "model_full": model,
        "position": position,
        "note": note,
        "timestamp": time.time(),
    }
    _model_log.append(entry)
    # Live visibility on stderr
    label = f"{role}: {entry['model']} ({position})"
    if note:
        label += f" [{note}]"
    print(f"[model] {label}", file=sys.stderr)


# ── Offline Brain ──────────────────────────────────────────────────────────

def _offline(prompt: str) -> str:
    """Dispatch a prompt to the deterministic offline brain."""
    from src.tools import offline_brain

    if "pytest test that" in prompt or "REPRODUCES the bug" in prompt:
        return offline_brain.offline_regressor(prompt)
    if "unified diff patch" in prompt or "ONLY the diff" in prompt:
        return offline_brain.offline_coder(prompt)
    return offline_brain.offline_planner(prompt)


# ── Chain Callers ──────────────────────────────────────────────────────────

# Providers that answered with a session-fatal error (quota exhausted, bad
# key).  Remaining models from the same provider are skipped instead of
# re-paying the same 429/403 for every step of every retry.
_dead_providers: set = set()

_AUTH_FATAL_TYPES = {
    "AuthenticationError",    # bad/expired key
    "PermissionDeniedError",  # key has no access to this provider
}
_MODEL_FATAL_TYPES = {
    "NotFoundError",     # this model id is gone — other models may still work
    "BadRequestError",   # prompt/model mismatch — retrying changes nothing
}
# A 429 is only provider-fatal when it is account quota/billing; a per-minute
# rate limit clears itself, so it is backed off and retried instead.  Match
# exact phrases — Groq's TPM error embeds a console.groq.com/settings/billing
# URL, so a bare "billing" hint would wrongly kill a healthy provider.
_QUOTA_HINTS = (
    "exceeded your current quota", "quota exceeded", "insufficient_quota",
    "exceeded your quota", "out of credit", "insufficient credit",
    "credit balance", "plan and billing",
)
_RETRYABLE_HINTS = (
    "timed out", "timeout", "temporarily", "unavailable", "connection",
    "overloaded", "503", "502", "500", "internal",
    "rate limit", "rate_limit", "too many requests", "requests per",
    "tokens per", "429",
)
_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = 40  # Groq free-tier TPM windows are ~30-60s


def _call_budget() -> float:
    """Wall-clock seconds one chain call may spend before moving on."""
    try:
        return float(os.getenv("ISHA_CALL_BUDGET", "300"))
    except ValueError:
        return 300.0


def _provider(model: str) -> str:
    """'groq/openai/gpt-oss-20b' → 'groq'."""
    return model.split("/", 1)[0] if "/" in model else model


def _provider_fatal(exc: Exception) -> bool:
    """Session-fatal for the whole provider (quota exhausted / bad key)."""
    name = type(exc).__name__
    if name in _AUTH_FATAL_TYPES:
        return True
    if name == "RateLimitError":
        msg = str(exc).lower()
        return any(h in msg for h in _QUOTA_HINTS)
    return False


def _model_fatal(exc: Exception) -> bool:
    """This model is unusable — move to the next entry in the chain."""
    return type(exc).__name__ in _MODEL_FATAL_TYPES


def _retryable(exc: Exception) -> bool:
    """Transient error (rate limit, timeout, 5xx) — wait and try again."""
    if _provider_fatal(exc) or _model_fatal(exc):
        return False
    return any(h in str(exc).lower() for h in _RETRYABLE_HINTS)


_RATE_LIMIT_HINTS = (
    "rate limit", "rate_limit", "too many requests", "requests per",
    "tokens per", "429", "tokens per min", "tokens per day",
)


def _is_rate_limit(exc: Exception) -> bool:
    """True for a TPM/RPM limit (as opposed to a hard quota failure)."""
    if type(exc).__name__ != "RateLimitError":
        return False
    msg = str(exc).lower()
    if any(h in msg for h in _QUOTA_HINTS):
        return False
    return True


def _backoff_wait(exc: Exception, attempt: int) -> int:
    """Seconds to wait before retrying — honour the provider's own hint."""
    match = re.search(r"try again in ([0-9]+(?:\.[0-9]+)?)s", str(exc), re.I)
    if match:
        return int(float(match.group(1)) + 2)
    return min(_BACKOFF_SECONDS * attempt, 120)


# A TPM window is shared by every model on a provider.  Recording it means a
# *later* call on the same provider sleeps out the remaining window instead
# of burning an attempt (and a chain position) rediscovering the same 429.
_RATE_COOLDOWN: dict = {}


def _note_rate_limit(provider: str, wait: float) -> None:
    until = time.monotonic() + max(wait, 0.0)
    if until > _RATE_COOLDOWN.get(provider, 0.0):
        _RATE_COOLDOWN[provider] = until


def _cooldown_remaining(provider: str) -> float:
    return max(0.0, _RATE_COOLDOWN.get(provider, 0.0) - time.monotonic())


def _call_chain(chain: list, role: str, prompt: str, temperature: float | None = None) -> str:
    """Try each model in *chain*; first success wins.

    Provider-fatal errors (429 quota, bad key) poison-mark the provider so
    every later step skips it instead of re-paying the same error.  Model-
    fatal errors (unknown model id, bad request) just advance the chain.
    Only transient infrastructure errors are retried (max 3 attempts).
    If every model fails, the offline brain answers so the run never
    hard-fails.  Every attempt is logged.

    ``temperature`` is optional sampling control for candidate generation;
    it never changes which models are tried.
    """
    if OFFLINE_MODE or litellm is None:
        _log_model(role, "offline-brain", "offline",
                   "no API keys or forced offline")
        try:
            return _offline(prompt)
        except Exception as e:
            return f"[{role.upper()} ERROR] offline: {e}"

    errors: list = []
    call_started = time.monotonic()
    if os.getenv("ISHA_PROMPT_STATS", "0") == "1":
        print(
            f"[model] {role}: prompt={len(prompt)} chars "
            f"chain={len(chain)} budget={_call_budget():.0f}s",
            file=sys.stderr,
        )
    for i, model in enumerate(chain):
        provider = _provider(model)
        if provider in _dead_providers:
            errors.append(f"{_short_name(model)}: skipped ({provider} unavailable)")
            print(
                f"[model] {role}: skipping {_short_name(model)} — "
                f"provider '{provider}' already marked unavailable",
                file=sys.stderr,
            )
            continue

        position = "primary" if i == 0 else f"fallback {i}"
        attempts = 0
        while True:
            attempts += 1
            # Sleep out a known-limited window before paying for a 429.
            cool = _cooldown_remaining(provider)
            if cool > 0:
                spent = time.monotonic() - call_started
                if spent + cool <= _call_budget():
                    print(
                        f"[model] {role}: {_short_name(model)} provider "
                        f"'{provider}' in rate-limit cooldown {cool:.0f}s",
                        file=sys.stderr,
                    )
                    time.sleep(cool)
                else:
                    print(
                        f"[model] {role}: {_short_name(model)} cooldown "
                        f"{cool:.0f}s exceeds remaining call budget — advancing",
                        file=sys.stderr,
                    )
                    break
            try:
                kwargs = dict(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    num_retries=0,
                    timeout=45,
                )
                if temperature is not None:
                    kwargs["temperature"] = temperature
                resp = litellm.completion(**kwargs)
                content = resp.choices[0].message.content
                if not content or content.strip().startswith(
                    ("[PLANNER ERROR", "[CODER ERROR", "[REGRESSION")
                ):
                    raise ValueError("empty or error response")
                _log_model(role, model, position)
                return content
            except Exception as e:
                err_name = type(e).__name__
                short_err = str(e)[:80].replace("\n", " ")
                errors.append(f"{_short_name(model)}: {err_name}")
                print(
                    f"[model] {role}: {_short_name(model)} ({position}) "
                    f"FAILED — {err_name}: {short_err}",
                    file=sys.stderr,
                )
                if _provider_fatal(e):
                    _dead_providers.add(provider)
                    print(
                        f"[model] provider '{provider}' marked unavailable "
                        f"for this session ({err_name})",
                        file=sys.stderr,
                    )
                    break
                if _model_fatal(e):
                    break  # this model is unusable — next chain entry
                if attempts >= _MAX_ATTEMPTS or not _retryable(e):
                    break
                # transient (rate limit / timeout / 5xx) — back off, retry
                wait = _backoff_wait(e, attempts)
                if time.monotonic() - call_started > _call_budget():
                    print(
                        f"[model] {role}: {_short_name(model)} out of call budget "
                        f"({_call_budget():.0f}s) — advancing to next model",
                        file=sys.stderr,
                    )
                    break
                if _is_rate_limit(e):
                    # A TPM/RPM window clears itself, and every model on the
                    # provider shares it — advancing would just burn the whole
                    # chain in seconds.  Wait (exponential, capped) and retry
                    # THIS model instead.
                    wait = min(wait, 60)
                    _note_rate_limit(provider, wait)
                    print(
                        f"[model] {role}: {_short_name(model)} rate limited — "
                        f"backoff {wait}s (attempt {attempts}/{_MAX_ATTEMPTS})",
                        file=sys.stderr,
                    )
                    time.sleep(wait)
                    continue
                if wait > 20:
                    print(
                        f"[model] {role}: {_short_name(model)} wait {wait}s too long "
                        f"— advancing to next model in fallback chain",
                        file=sys.stderr,
                    )
                    break
                print(
                    f"[model] {role}: {_short_name(model)} transient — "
                    f"waiting {wait}s before retry {attempts + 1}/{_MAX_ATTEMPTS}",
                    file=sys.stderr,
                )
                time.sleep(wait)

    # All chain models failed or were unavailable — offline brain is the net.
    note = f"chain exhausted ({len(chain)} models): {'; '.join(errors)}"
    _log_model(role, "offline-brain", "offline", note)
    try:
        return _offline(prompt)
    except Exception as offline_err:
        return f"[{role.upper()} ERROR] chain exhausted / offline: {offline_err}"


def call_planner(prompt: str, temperature: float | None = None) -> str:
    """Call the planner model chain for planning and reasoning."""
    return _call_chain(PLANNER_CHAIN, "planner", prompt, temperature)


def call_coder(prompt: str, temperature: float | None = None) -> str:
    """Call the coder model chain for patch generation."""
    return _call_chain(CODER_CHAIN, "coder", prompt, temperature)


def offline_calls(since: int = 0) -> list:
    """Model-log entries where the deterministic offline brain answered.

    Used by the benchmark to tell "no live model could answer" (an API
    failure) apart from a genuine model response.
    """
    return [e for e in _model_log[since:] if e.get("position") == "offline"]


def reset_provider_state() -> None:
    """Forget session-scoped provider failures.

    Benchmark instances are independent: a provider marked unavailable for
    one instance should get a fresh chance on the next one, otherwise a single
    transient quota error would poison the rest of the run.
    """
    _dead_providers.clear()


def provider_dead() -> list:
    """Providers currently marked unavailable for this session."""
    return sorted(_dead_providers)


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
