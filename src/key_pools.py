"""
ISHA Key Pool Management — Multi-key rotation, quota isolation, and cooldown revival.

Maintains thread-safe rotating pools across multiple providers (Gemini, Groq,
OpenRouter, Cerebras). Tracks per-model rate limits and revives keys after cooldown.
"""

from __future__ import annotations

import collections
import os
import sys
import threading
import time
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]

# ── Model availability & Key Pools ──────────────────────────────────────────
_gemini_keys_raw = (
    os.getenv("GEMINI_API_KEYS")
    or os.getenv("GOOGLE_API_KEY")
    or os.getenv("GEMINI_API_KEY")
    or ""
)
_gemini_key_pool = [k.strip() for k in _gemini_keys_raw.split(",") if k.strip()]
_gemini_key_lock = threading.Lock()
_gemini_key_counter = 0
_dead_gemini_keys: set = set()
_dead_gemini_keys_by_model: dict = collections.defaultdict(set)
_key_death_time: dict = {}
_env_last_mtime: float = 0.0

GOOGLE_API_KEY = _gemini_key_pool[0] if _gemini_key_pool else None

# Groq/OpenRouter/Cerebras pools
_groq_keys_raw = os.getenv("GROQ_API_KEYS") or os.getenv("GROQ_API_KEY") or ""
_groq_key_pool = [k.strip() for k in _groq_keys_raw.split(",") if k.strip()]
_groq_key_lock = threading.Lock()
_groq_key_counter = 0

_openrouter_keys_raw = os.getenv("OPENROUTER_API_KEYS") or os.getenv("OPENROUTER_API_KEY") or ""
_openrouter_key_pool = [k.strip() for k in _openrouter_keys_raw.split(",") if k.strip()]
_openrouter_key_lock = threading.Lock()
_openrouter_key_counter = 0

_cerebras_keys_raw = os.getenv("CEREBRAS_API_KEYS") or os.getenv("CEREBRAS_API_KEY") or ""
_cerebras_key_pool = [k.strip() for k in _cerebras_keys_raw.split(",") if k.strip()]
_cerebras_key_lock = threading.Lock()
_cerebras_key_counter = 0

GROQ_API_KEY = _groq_key_pool[0] if _groq_key_pool else None
OPENROUTER_API_KEY = _openrouter_key_pool[0] if _openrouter_key_pool else None
MISTRAL_API_KEY = None
CEREBRAS_API_KEY = _cerebras_key_pool[0] if _cerebras_key_pool else None

LLM_ENABLED = bool(GOOGLE_API_KEY or GROQ_API_KEY or OPENROUTER_API_KEY or CEREBRAS_API_KEY)
OFFLINE_MODE = (not LLM_ENABLED) or os.getenv("ISHA_FORCE_OFFLINE", "0") == "1"


def _next_from_pool(pool: list, lock: threading.Lock, counter_name: str) -> str | None:
    """Round-robin pick from a key pool."""
    global _groq_key_counter, _openrouter_key_counter, _cerebras_key_counter
    if not pool:
        return None
    with lock:
        if counter_name == "groq":
            _groq_key_counter += 1
            return pool[_groq_key_counter % len(pool)]
        elif counter_name == "openrouter":
            _openrouter_key_counter += 1
            return pool[_openrouter_key_counter % len(pool)]
        elif counter_name == "cerebras":
            _cerebras_key_counter += 1
            return pool[_cerebras_key_counter % len(pool)]
        return pool[0]


_dead_groq_keys = set()
_dead_groq_keys_by_model: dict = collections.defaultdict(set)
_groq_key_death_time: dict = {}


def get_next_groq_key(model: str = "") -> str | None:
    """Return next active Groq API key in round-robin order, isolating quota per-model."""
    global _groq_key_counter
    with _groq_key_lock:
        now = time.time()
        dead = _dead_groq_keys_by_model[model] if model else _dead_groq_keys
        revived = [k for k in list(dead) if (now - _groq_key_death_time.get((k, model), 0.0)) > 60]
        for k in revived:
            dead.remove(k)
            _groq_key_death_time.pop((k, model), None)
        active = [k for k in _groq_key_pool if k not in dead]
        if not active:
            active = _groq_key_pool
        if not active:
            return None
        _groq_key_counter += 1
        return active[_groq_key_counter % len(active)]


def mark_groq_key_dead(key: str, model: str = "") -> bool:
    """Mark a Groq key as rate-limited/exhausted."""
    with _groq_key_lock:
        if model:
            _dead_groq_keys_by_model[model].add(key)
            _groq_key_death_time[(key, model)] = time.time()
            active = [k for k in _groq_key_pool if k not in _dead_groq_keys_by_model[model]]
            return len(active) > 0
        else:
            _dead_groq_keys.add(key)
            _groq_key_death_time[(key, "")] = time.time()
            active = [k for k in _groq_key_pool if k not in _dead_groq_keys]
            return len(active) > 0


def get_next_openrouter_key() -> str | None:
    return _next_from_pool(_openrouter_key_pool, _openrouter_key_lock, "openrouter")


def get_next_mistral_key() -> str | None:
    return None


def get_next_cerebras_key() -> str | None:
    return _next_from_pool(_cerebras_key_pool, _cerebras_key_lock, "cerebras")


def _check_and_reload_keys_from_env() -> None:
    """Dynamically re-read .env if changed on disk, adding any newly added keys."""
    global _gemini_key_pool, _cerebras_key_pool, _env_last_mtime
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    try:
        mtime = env_file.stat().st_mtime
        if mtime > _env_last_mtime:
            _env_last_mtime = mtime
            load_dotenv(dotenv_path=env_file, override=True)
            raw = (
                os.getenv("GEMINI_API_KEYS")
                or os.getenv("GOOGLE_API_KEY")
                or os.getenv("GEMINI_API_KEY")
                or ""
            )
            fresh_keys = [k.strip() for k in raw.split(",") if k.strip()]
            if fresh_keys != _gemini_key_pool:
                _gemini_key_pool = fresh_keys
                _dead_gemini_keys_by_model.clear()
                print(
                    f"[config] Reloaded {len(fresh_keys)} Gemini keys into active pool",
                    file=sys.stderr,
                )
            craw = os.getenv("CEREBRAS_API_KEYS") or os.getenv("CEREBRAS_API_KEY") or ""
            _cerebras_key_pool = [k.strip() for k in craw.split(",") if k.strip()]
    except Exception:
        pass


def get_next_gemini_key(model: str = "") -> str | None:
    """Return next active Gemini API key in round-robin order, isolating quota per-model."""
    global _gemini_key_counter
    with _gemini_key_lock:
        _check_and_reload_keys_from_env()
        now = time.time()
        dead_for_model = _dead_gemini_keys_by_model[model] if model else _dead_gemini_keys
        revived = [
            k for k in list(dead_for_model)
            if (now - _key_death_time.get((k, model), 0.0)) > 25
        ]
        for k in revived:
            dead_for_model.remove(k)
            _key_death_time.pop((k, model), None)
            print(f"[config] Revived Gemini key {k[:6]}... for {model or 'all'} after cooldown", file=sys.stderr)

        active = [k for k in _gemini_key_pool if k not in dead_for_model]
        if not active:
            active = [k for k in _gemini_key_pool if k not in _dead_gemini_keys]
            if not active:
                active = _gemini_key_pool
        if not active:
            return None
        _gemini_key_counter += 1
        return active[_gemini_key_counter % len(active)]


def mark_gemini_key_dead(key: str, model: str = "") -> bool:
    """Mark a Gemini key as quota-exhausted for this specific model."""
    with _gemini_key_lock:
        if model:
            _dead_gemini_keys_by_model[model].add(key)
            _key_death_time[(key, model)] = time.time()
            active = [k for k in _gemini_key_pool if k not in _dead_gemini_keys_by_model[model]]
            print(
                f"[config] Gemini key {key[:6]}... quota exhausted for {model} ({len(active)} active keys remaining for {model})",
                file=sys.stderr,
            )
            return len(active) > 0
        else:
            _dead_gemini_keys.add(key)
            active = [k for k in _gemini_key_pool if k not in _dead_gemini_keys]
            print(
                f"[config] Gemini key {key[:6]}... quota exhausted ({len(active)} active keys remaining)",
                file=sys.stderr,
            )
            return len(active) > 0


def reset_key_pools() -> None:
    """Reset dead key registries and cooldown timers across all key pools."""
    with _gemini_key_lock:
        _dead_gemini_keys.clear()
        _dead_gemini_keys_by_model.clear()
        _key_death_time.clear()
    with _groq_key_lock:
        _dead_groq_keys.clear()
        _dead_groq_keys_by_model.clear()
        _groq_key_death_time.clear()


def _rotate_gemini_key() -> bool:
    """Return True if any active Gemini key remains."""
    with _gemini_key_lock:
        active = [k for k in _gemini_key_pool if k not in _dead_gemini_keys]
        return len(active) > 0

