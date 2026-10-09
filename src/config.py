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
import threading
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
    "ISHA_PLANNER_MODEL", "gemini/gemini-3.5-flash-lite",
    "ISHA_PLANNER_FALLBACKS",
    "gemini/gemini-3.8-flash,gemini/gemini-3.5-flash",
)

CODER_CHAIN = _parse_chain(
    "ISHA_CODER_MODEL", "gemini/gemini-3.5-flash-lite",
    "ISHA_CODER_FALLBACKS",
    "gemini/gemini-3.8-flash,gemini/gemini-3.5-flash",
)

LOCALIZER_CHAIN = _parse_chain(
    "ISHA_LOCALIZER_MODEL", "gemini/gemini-3.5-flash-lite",
    "ISHA_LOCALIZER_FALLBACKS",
    "gemini/gemini-3.8-flash,gemini/gemini-3.5-flash",
)

CRITIC_CHAIN = _parse_chain(
    "ISHA_CRITIC_MODEL", "gemini/gemini-3.8-flash",
    "ISHA_CRITIC_FALLBACKS",
    "gemini/gemini-3.5-flash-lite,gemini/gemini-3.5-flash",
)

# Backward-compatible aliases
PLANNER_MODEL = PLANNER_CHAIN[0]
CODER_MODEL = CODER_CHAIN[0]
LOCALIZER_MODEL = LOCALIZER_CHAIN[0]
CRITIC_MODEL = CRITIC_CHAIN[0]
PLANNER_FALLBACKS = PLANNER_CHAIN[1:]
CODER_FALLBACKS = CODER_CHAIN[1:]

# Candidate models for Multi-Model Arbitration (Phase 4 / Ensemble Mode)
CANDIDATE_1_MODEL = os.getenv("ISHA_CANDIDATE_1_MODEL", "gemini/gemini-3.5-flash-lite")
CANDIDATE_2_MODEL = os.getenv("ISHA_CANDIDATE_2_MODEL", "gemini/gemini-3.8-flash")
CANDIDATE_3_MODEL = os.getenv("ISHA_CANDIDATE_3_MODEL", "gemini/gemini-3.5-flash-lite")

# Architecture defaults: 3 diverse tournament candidates by default
DEFAULT_CANDIDATES = int(os.getenv("ISHA_CANDIDATES", "3"))
DEFAULT_IMPROVE_ROUNDS = int(os.getenv("ISHA_IMPROVE_ROUNDS", "3"))
DEFAULT_CONVERGENCE_DELTA = float(os.getenv("ISHA_CONVERGENCE_DELTA", "0.0"))


# ── Model availability ─────────────────────────────────────────────────────
_gemini_keys_raw = os.getenv("GEMINI_API_KEYS") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
_gemini_key_pool = [k.strip() for k in _gemini_keys_raw.split(",") if k.strip()]
_gemini_key_lock = threading.Lock()
_gemini_key_counter = 0
_dead_gemini_keys: set = set()

GOOGLE_API_KEY = _gemini_key_pool[0] if _gemini_key_pool else None
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_ENABLED = bool(GOOGLE_API_KEY or GROQ_API_KEY or OPENROUTER_API_KEY)
OFFLINE_MODE = (not LLM_ENABLED) or os.getenv("ISHA_FORCE_OFFLINE", "0") == "1"


def get_next_gemini_key() -> str | None:
    """Return next active Gemini API key in round-robin order across threads."""
    global _gemini_key_counter
    with _gemini_key_lock:
        active = [k for k in _gemini_key_pool if k not in _dead_gemini_keys]
        if not active:
            return None
        _gemini_key_counter += 1
        return active[_gemini_key_counter % len(active)]


def mark_gemini_key_dead(key: str) -> bool:
    """Mark a Gemini key as quota-exhausted. Returns True if any active keys remain."""
    with _gemini_key_lock:
        _dead_gemini_keys.add(key)
        active = [k for k in _gemini_key_pool if k not in _dead_gemini_keys]
        print(f"[config] Gemini key {key[:12]}... quota exhausted ({len(active)} active keys remaining)", file=sys.stderr)
        return len(active) > 0


def _rotate_gemini_key() -> bool:
    """Return True if any active Gemini key remains."""
    with _gemini_key_lock:
        active = [k for k in _gemini_key_pool if k not in _dead_gemini_keys]
        return len(active) > 0


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

# Per-thread by design: benchmark runs solve instances in parallel and the
# candidate tournament already calls models from worker threads.  A shared
# list would let one instance's ``clear_model_log()`` wipe another thread's
# audit trail mid-flight, so each thread keeps its own log.
_tls = threading.local()


def _model_log() -> list:
    log = getattr(_tls, "model_log", None)
    if log is None:
        log = []
        _tls.model_log = log
    return log


def get_model_log() -> list:
    """Return the ordered model-usage entries for this thread."""
    return list(_model_log())


def clear_model_log() -> None:
    """Reset this thread's model log for a new run."""
    _model_log().clear()


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
        # Candidates run in parallel threads; without this a candidate can
        # attribute another thread's answer to itself.
        "thread": threading.current_thread().name,
        "timestamp": time.time(),
    }
    _model_log().append(entry)
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
# Models whose ACCOUNT QUOTA died (a 429 carrying "exceeded your current
# quota" / "plan and billing").  Gemini quotas are per-model: killing the
# whole provider would skip flash-lite, which has its own bucket and still
# works — so the last-resort fallback becomes unreachable exactly when it is
# needed.  Session-scoped (daily quotas do not recover mid-run), and unlike
# a provider death it is never cleared by ``reset_provider_state()``.
_dead_models: set = set()

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


def _quota_fatal(exc: Exception) -> bool:
    """Account quota/billing exhausted for THIS model (not a transient RPM/TPM window)."""
    msg = str(exc).lower()
    # If the error explicitly mentions per-minute or per-day sliding window, it's transient
    if any(m in msg for m in ("per minute", "per_minute", "queries per minute", "requests per minute", "tpm", "rpm")):
        return False
    return type(exc).__name__ == "RateLimitError" and any(
        h in msg for h in _QUOTA_HINTS
    )


def _provider_fatal(exc: Exception) -> bool:
    """Session-fatal for the whole provider (quota exhausted / bad key)."""
    name = type(exc).__name__
    if name in _AUTH_FATAL_TYPES:
        return True
    return _quota_fatal(exc)


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


import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LLM_CACHE_DIR = ROOT / "data" / "cache" / "llm"


def _cache_key(model: str, prompt: str, temperature: float | None) -> str:
    temp_str = f"{temperature:.2f}" if temperature is not None else "default"
    return hashlib.sha256(f"{model}:{temp_str}:{prompt}".encode("utf-8")).hexdigest()


def _get_cached_llm(model: str, prompt: str, temperature: float | None) -> str | None:
    if os.getenv("ISHA_DISABLE_LLM_CACHE", "0") == "1":
        return None
    key = _cache_key(model, prompt, temperature)
    f = LLM_CACHE_DIR / f"{key}.json"
    if f.is_file():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            return data.get("response")
        except Exception:
            return None
    return None


def _set_cached_llm(model: str, prompt: str, temperature: float | None, response: str) -> None:
    if os.getenv("ISHA_DISABLE_LLM_CACHE", "0") == "1" or not response:
        return
    LLM_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = _cache_key(model, prompt, temperature)
    f = LLM_CACHE_DIR / f"{key}.json"
    try:
        f.write_text(json.dumps({
            "model": model,
            "temperature": temperature,
            "response": response,
            "cached_at": time.time(),
        }, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _advance_on_rate_limit() -> bool:
    """Should a 429 advance the chain instead of sleeping and retrying?"""
    if os.getenv("ISHA_RATE_LIMIT_WAIT", "").strip() in ("1", "true", "yes"):
        return False
    return True


# ── Per-call event stream (bench forensics, v2.1) ─────────────────────────
# Under 429 storms an attempt can burn its whole wall budget inside backoff
# sleeps with zero completed model calls, and the in-flight entries were
# previously lost when the attempt died (FutureTimeout discards the worker's
# model log).  Every meaningful chain step now emits an event; callers may
# attach a sink (the bench runner streams them to the instance's log.jsonl
# as they happen) and an attempt deadline that aborts a chain which has made
# no model progress for a fraction of the attempt budget.
_events_tls = threading.local()


def _call_event(role: str, model: str, position: str, outcome: str, note: str = "") -> None:
    ev = {
        "ts": time.time(),
        "role": role,
        "model": model,
        "position": position,
        "outcome": outcome,
        "note": (note or "")[:200],
    }
    store = getattr(_events_tls, "list", None)
    if store is None:
        store = _events_tls.list = []
    store.append(ev)
    sink = getattr(_events_tls, "sink", None)
    if sink is not None:
        try:
            sink(ev)
        except Exception:
            pass


def get_call_events() -> list:
    """Copy of the current thread's per-call event list."""
    store = getattr(_events_tls, "list", None)
    return list(store) if store else []


def reset_call_events() -> None:
    """Clear events/sink/deadline for the current thread (start of an attempt)."""
    _events_tls.list = []
    _events_tls.sink = None
    _events_tls.deadline = None
    _events_tls.deadline_start = None
    _events_tls.ok_seen = False


def set_call_event_sink(fn) -> None:
    """Attach a per-event sink (must be fast and never raise)."""
    _events_tls.sink = fn


def set_attempt_deadline(seconds: float | None) -> None:
    """Per-thread attempt deadline (monotonic). None disables it."""
    if seconds:
        _events_tls.deadline = float(seconds)
        _events_tls.deadline_start = time.monotonic()
    else:
        _events_tls.deadline = None
        _events_tls.deadline_start = None


def _attempt_deadline_hit() -> bool:
    """True once the attempt spent frac*deadline with no successful model call."""
    deadline = getattr(_events_tls, "deadline", None)
    if not deadline:
        return False
    if getattr(_events_tls, "ok_seen", False):
        return False
    start = getattr(_events_tls, "deadline_start", None)
    if start is None:
        start = time.monotonic()
        _events_tls.deadline_start = start
    frac = float(os.getenv("ISHA_ATTEMPT_DEADLINE_FRAC", "0.6"))
    return (time.monotonic() - start) > frac * deadline


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
        _call_event(role, "offline-brain", "offline", "offline",
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
        if _attempt_deadline_hit():
            # The attempt has burned most of its wall budget without a single
            # model answering (backoff-dominated storm).  Stop paying for more
            # chain positions and hand back the offline answer early — the
            # bench runner's retry logic then gets a fresh attempt sooner.
            errors.append("attempt deadline reached with no model progress")
            print(
                f"[model] {role}: attempt deadline reached with no model "
                f"progress — aborting chain early",
                file=sys.stderr,
            )
            _call_event(role, chain[i] if i < len(chain) else "?", "chain",
                        "deadline_aborted", "attempt_deadline_no_model_progress")
            break
        provider = _provider(model)
        if provider in _dead_providers:
            errors.append(f"{_short_name(model)}: skipped ({provider} unavailable)")
            print(
                f"[model] {role}: skipping {_short_name(model)} — "
                f"provider '{provider}' already marked unavailable",
                file=sys.stderr,
            )
            _call_event(role, _short_name(model), "skipped", "skipped",
                        f"provider '{provider}' unavailable")
            continue
        if model in _dead_models:
            errors.append(f"{_short_name(model)}: skipped (model quota exhausted)")
            print(
                f"[model] {role}: skipping {_short_name(model)} — "
                f"model quota exhausted for this session",
                file=sys.stderr,
            )
            _call_event(role, _short_name(model), "skipped", "skipped",
                        "model quota exhausted")
            continue

        position = "primary" if i == 0 else f"fallback {i}"
        cached = _get_cached_llm(model, prompt, temperature)
        if cached:
            _log_model(role, model, f"{position} [cached]")
            _events_tls.ok_seen = True
            _call_event(role, _short_name(model), f"{position} [cached]", "ok",
                        "cache hit")
            return cached

        attempts = 0
        while True:
            attempts += 1
            # Sleep out a known-limited window before paying for a 429.
            cool = _cooldown_remaining(provider)
            if cool > 0:
                if _advance_on_rate_limit():
                    print(
                        f"[model] {role}: {_short_name(model)} provider "
                        f"'{provider}' in rate-limit cooldown {cool:.0f}s — advancing",
                        file=sys.stderr,
                    )
                    break
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
                active_gemini_key = None
                if provider == "gemini":
                    active_gemini_key = get_next_gemini_key()
                    if active_gemini_key:
                        kwargs["api_key"] = active_gemini_key
                resp = litellm.completion(**kwargs)
                content = resp.choices[0].message.content
                if not content or content.strip().startswith(
                    ("[PLANNER ERROR", "[CODER ERROR", "[REGRESSION")
                ):
                    raise ValueError("empty or error response")
                _log_model(role, model, position)
                _set_cached_llm(model, prompt, temperature, content)
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
                    if _quota_fatal(e):
                        if provider == "gemini" and active_gemini_key:
                            if mark_gemini_key_dead(active_gemini_key):
                                # Successfully marked key dead, other keys remain — retry call immediately
                                continue
                        # Per-model quota — kill the model, not the provider
                        _dead_models.add(model)
                        print(
                            f"[model] {_short_name(model)} quota exhausted — "
                            f"skipping it for the rest of this session "
                            f"({err_name})",
                            file=sys.stderr,
                        )
                    else:
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
                    if _advance_on_rate_limit():
                        # A measurement run is throughput-bound: a 40-60s
                        # sleep per call is most of the instance budget, and
                        # the fallback is warm.  Record the window so later
                        # calls skip this provider outright, then move on.
                        print(
                            f"[model] {role}: {_short_name(model)} rate limited "
                            f"— marking '{provider}' rate-limited for {wait:.0f}s "
                            f"and advancing",
                            file=sys.stderr,
                        )
                        break
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


def call_coder(
    prompt: str,
    temperature: float | None = None,
    model: str | None = None,
) -> str:
    """Call the coder model chain for patch generation.

    If ``model`` is specified, that model is tried first, followed by the rest
    of the fallback chain if it fails or rate-limits.
    """
    if model:
        chain = [model] + [m for m in CODER_CHAIN if m != model]
    else:
        chain = CODER_CHAIN
    return _call_chain(chain, "coder", prompt, temperature)


def offline_calls(since: int = 0) -> list:
    """Model-log entries where the deterministic offline brain answered.

    Used by the benchmark to tell "no live model could answer" (an API
    failure) apart from a genuine model response.
    """
    return [e for e in _model_log()[since:] if e.get("position") == "offline"]


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
