import json
import os
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# We test Groq, Gemini, and OpenRouter
import litellm
litellm.suppress_debug_info = True

def mask_key(k: str) -> str:
    if len(k) <= 10:
        return k[:3] + "..." + k[-3:]
    return k[:6] + "..." + k[-4:]

def test_groq_key(key: str, model: str = "groq/openai/gpt-oss-120b"):
    t0 = time.time()
    try:
        r = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": "Respond strictly with: PONG"}],
            api_key=key,
            timeout=10,
        )
        dt = round(time.time() - t0, 2)
        txt = r.choices[0].message.content.strip().replace("\n", " ")[:35]
        return "WORKING", dt, txt
    except Exception as e:
        dt = round(time.time() - t0, 2)
        err_type = type(e).__name__
        err_msg = str(e).replace("\n", " ")[:120]
        if "RateLimitError" in err_type or "429" in err_msg or "rate limit" in err_msg.lower():
            return "RATE_LIMITED", dt, f"{err_type}: {err_msg}"
        if "AuthenticationError" in err_type or "401" in err_msg:
            return "AUTH_FAILED", dt, f"{err_type}: {err_msg}"
        return "ERROR", dt, f"{err_type}: {err_msg}"


def test_gemini_key_rest(key: str, model: str = "gemini-2.5-flash"):
    # Direct REST call to Google generative language endpoint to avoid litellm proxy artifacts
    t0 = time.time()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": "Respond strictly with: PONG"}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 20}
    }
    headers = {"Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=12)
        dt = round(time.time() - t0, 2)
        if r.status_code == 200:
            data = r.json()
            try:
                txt = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception:
                txt = "OK"
            return "WORKING", dt, txt
        elif r.status_code == 429:
            return "RATE_LIMITED", dt, f"HTTP 429: {r.text[:100]}"
        elif r.status_code in (401, 403):
            return "AUTH_FAILED", dt, f"HTTP {r.status_code}: {r.text[:100]}"
        else:
            return "ERROR", dt, f"HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        dt = round(time.time() - t0, 2)
        err_type = type(e).__name__
        return "TIMEOUT/CONN_ERR", dt, f"{err_type}: {str(e)[:100]}"

def test_openrouter_key(key: str):
    t0 = time.time()
    try:
        r = requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
        dt = round(time.time() - t0, 2)
        if r.status_code == 200:
            d = r.json().get("data", {})
            limit = d.get("limit")
            usage = d.get("usage")
            return "WORKING", dt, f"Usage: ${usage} / Limit: ${limit}"
        return "AUTH_FAILED", dt, f"HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        dt = round(time.time() - t0, 2)
        return "ERROR", dt, str(e)[:100]

def main():
    print("=" * 60)
    print("        ISHA COMPREHENSIVE API KEY AUDIT")
    print("=" * 60)

    # 1. Groq Keys
    groq_raw = os.getenv("GROQ_API_KEYS") or os.getenv("GROQ_API_KEY") or ""
    groq_keys = [k.strip() for k in groq_raw.split(",") if k.strip()]
    print(f"\n[1] GROQ KEYS ({len(groq_keys)} keys configured)")
    for i, k in enumerate(groq_keys, 1):
        status, dt, note = test_groq_key(k)
        print(f"  Key #{i} [{mask_key(k)}]: [{status}] ({dt}s) -> {note}")

    # 2. Gemini Keys
    gemini_raw = os.getenv("GEMINI_API_KEYS") or os.getenv("GOOGLE_API_KEY") or ""
    gemini_keys = [k.strip() for k in gemini_raw.split(",") if k.strip()]
    print(f"\n[3] GOOGLE GEMINI KEYS ({len(gemini_keys)} keys configured)")
    for i, k in enumerate(gemini_keys, 1):
        status, dt, note = test_gemini_key_rest(k, "gemini-2.5-flash")
        print(f"  Key #{i} [{mask_key(k)}]: [{status}] ({dt}s) -> {note}")

    # 4. OpenRouter Key
    or_key = os.getenv("OPENROUTER_API_KEY", "")
    if or_key:
        print(f"\n[4] OPENROUTER KEY")
        status, dt, note = test_openrouter_key(or_key)
        print(f"  OpenRouter [{mask_key(or_key)}]: [{status}] ({dt}s) -> {note}")

if __name__ == "__main__":
    main()

