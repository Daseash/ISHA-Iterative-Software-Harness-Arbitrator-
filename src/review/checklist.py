"""
ISHA Security & Performance Checklist — the critic's senior-dev instincts.

A lightweight LLM review of the diff itself: does this patch introduce an
injection risk, an N+1 query, a memory leak, swallowed exceptions? Runs in
addition to the LAYA scorer and guardrail secret-scan, and can veto a patch
that would otherwise score well.
"""

from __future__ import annotations

import re

_PROMPT = """You are a senior engineer reviewing a proposed patch diff.
Answer each item with PASS, RISK, or FAIL plus a one-line reason:

- SECURITY: injection, secrets/credentials, path traversal, unsafe eval/exec, shell=True
- PERFORMANCE: N+1 queries, unbounded loops / memory growth, blocking calls in hot paths
- ROBUSTNESS: swallowed exceptions, mutable default args, off-by-one, race conditions

End with exactly one line: VERDICT: PASS or VERDICT: BLOCK
Use BLOCK only when this diff clearly introduces a security hole or a
performance landmine. Style nits are never BLOCK.

BUG REPORT:
{issue}

PATCH:
{patch}
"""


def security_perf_checklist(issue_text: str, patch: str) -> dict | None:
    """Run the checklist; returns {"verdict": PASS|BLOCK, "review": text} or None."""
    from src.config import LLM_ENABLED, call_planner

    if not LLM_ENABLED or not patch:
        return None
    try:
        raw = call_planner(
            _PROMPT.format(issue=(issue_text or "")[:2000], patch=patch[:5000])
        )
    except Exception:
        return None

    match = re.search(r"VERDICT:\s*(PASS|BLOCK)", raw or "", re.IGNORECASE)
    if not match:
        return None
    return {
        "verdict": match.group(1).upper(),
        "review": (raw or "").strip()[:1400],
    }
