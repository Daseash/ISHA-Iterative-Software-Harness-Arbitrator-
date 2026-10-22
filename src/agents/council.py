"""
ISHA LLM Council — Multi-model deliberation engine.
Inspired by Andrej Karpathy's llm-council (https://github.com/karpathy/llm-council).

Three-stage deliberation pipeline:
1. Stage 1 (First Opinions): Multiple models answer independently in parallel.
2. Stage 2 (Blind Peer Review): Each model reviews, critiques, and ranks anonymized responses.
3. Stage 3 (Chairman Synthesis): A designated Chairman model synthesizes all opinions
   and peer reviews into a single, comprehensive, high-confidence consensus.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.config import (
    call_with_timeout,
    _short_name,
    PLANNER_CHAIN,
    CODER_CHAIN,
    LLM_ENABLED,
)

DEFAULT_COUNCIL = [
    "gemini/gemini-3.5-flash-lite",
    "gemini/gemini-3.8-flash",
    "groq/openai/gpt-oss-120b",
]

DEFAULT_CHAIRMAN = "gemini/gemini-3.8-flash"


@dataclass
class CouncilResult:
    query: str
    stage1_opinions: Dict[str, str]  # model_name -> response
    stage2_reviews: Dict[str, str]   # model_name -> critique/ranking of others
    stage3_synthesis: str            # Chairman's final synthesized consensus
    chairman: str
    duration_sec: float
    metadata: Dict[str, Any] = field(default_factory=dict)


def _call_model_safe(model: str, prompt: str, timeout: int = 45) -> tuple[str, str]:
    """Helper to call a model safely returning (model_name, response_text)."""
    from src.config import _call_chain, PLANNER_CHAIN
    try:
        chain = [model] + [m for m in PLANNER_CHAIN if m != model]
        resp = _call_chain(chain, "council", prompt)
        if resp and not resp.startswith("[COUNCIL ERROR]"):
            return model, resp.strip()
    except Exception:
        pass
    try:
        from src.config import call_with_timeout
        resp = call_with_timeout(model, prompt, timeout=timeout)
        if resp:
            return model, resp.strip()
    except Exception as exc:
        return model, f"[Council Error with {model}]: {exc}"
    return model, "[Council Unavailable]"


class LLMCouncil:
    """Orchestrates multi-model deliberation and consensus synthesis."""

    def __init__(
        self,
        council_models: Optional[List[str]] = None,
        chairman_model: Optional[str] = None,
    ):
        self.council_models = council_models or [
            m for m in DEFAULT_COUNCIL if m
        ]
        self.chairman_model = chairman_model or DEFAULT_CHAIRMAN

    def deliberate(self, query: str, timeout_per_stage: int = 45) -> CouncilResult:
        """Run the full 3-stage Council deliberation on a query."""
        t0 = time.time()

        # ── STAGE 1: First Opinions (Parallel) ─────────────────────────────
        stage1_opinions: Dict[str, str] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.council_models)) as executor:
            future_to_model = {
                executor.submit(
                    _call_model_safe,
                    model,
                    f"You are an expert software engineer on the AI Council.\n\n"
                    f"Question/Task:\n{query}\n\n"
                    f"Provide your clearest, most rigorous, and technically precise answer with necessary code or steps:",
                    timeout_per_stage,
                ): model
                for model in self.council_models
            }
            for future in concurrent.futures.as_completed(future_to_model):
                model, response = future.result()
                stage1_opinions[_short_name(model)] = response

        # ── STAGE 2: Blind Peer Review ─────────────────────────────────────
        # Anonymize opinions as Model A, Model B, Model C
        anonymized_labels = {}
        anonymized_text_blocks = []
        for idx, (model_name, opinion) in enumerate(stage1_opinions.items(), start=1):
            label = f"Response {chr(64 + idx)}"  # Response A, Response B...
            anonymized_labels[label] = model_name
            anonymized_text_blocks.append(f"### {label}:\n{opinion}\n")

        peer_review_context = "\n".join(anonymized_text_blocks)
        peer_review_prompt = (
            f"You are serving as a peer reviewer on the AI Council.\n\n"
            f"Original Query:\n{query}\n\n"
            f"Here are anonymized responses from other council members:\n"
            f"{peer_review_context}\n\n"
            f"Critique and compare these responses:\n"
            f"1. Identify any technical inaccuracies, hallucinations, or unhandled edge cases.\n"
            f"2. Highlight unique strengths or insights in each response.\n"
            f"3. Rank the responses from best to worst with brief justification."
        )

        stage2_reviews: Dict[str, str] = {}
        # Pick up to 2 models to run peer review in parallel
        reviewers = self.council_models[:2]
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(reviewers)) as executor:
            future_to_reviewer = {
                executor.submit(_call_model_safe, model, peer_review_prompt, timeout_per_stage): model
                for model in reviewers
            }
            for future in concurrent.futures.as_completed(future_to_reviewer):
                model, review = future.result()
                stage2_reviews[_short_name(model)] = review

        # ── STAGE 3: Chairman Synthesis ────────────────────────────────────
        reviews_summary = "\n\n".join(
            f"Peer Review by Reviewer {i}:\n{rev}"
            for i, rev in enumerate(stage2_reviews.values(), start=1)
        )

        chairman_prompt = (
            f"You are the Chairman of the AI Council.\n\n"
            f"User's Query:\n{query}\n\n"
            f"STAGE 1 (Council Members' Individual Responses):\n"
            f"{peer_review_context}\n\n"
            f"STAGE 2 (Blind Peer Reviews & Critiques):\n"
            f"{reviews_summary}\n\n"
            f"STAGE 3 (Chairman Synthesis Task):\n"
            f"Synthesize the single best, authoritative, comprehensive, and definitive consensus answer.\n"
            f"Resolve any contradictions between models, adopt the most accurate technical details, "
            f"and present a clear, actionable solution for the user."
        )

        _, stage3_synthesis = _call_model_safe(self.chairman_model, chairman_prompt, timeout=60)

        duration = time.time() - t0
        return CouncilResult(
            query=query,
            stage1_opinions=stage1_opinions,
            stage2_reviews=stage2_reviews,
            stage3_synthesis=stage3_synthesis,
            chairman=_short_name(self.chairman_model),
            duration_sec=duration,
            metadata={"anonymized_map": anonymized_labels},
        )


def ask_council(query: str) -> CouncilResult:
    """Convenience wrapper to run an LLM Council deliberation."""
    council = LLMCouncil()
    return council.deliberate(query)


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How does ISHA arbitrate between minimal_diff and root_cause_first patches?"
    print(f"\n🏛️  Summoning LLM Council for:\n   '{q}'\n")
    res = ask_council(q)
    print("=" * 70)
    print(f"🏛️  CHAIRMAN SYNTHESIS (Consensus by {res.chairman} in {res.duration_sec:.1f}s):")
    print("=" * 70)
    print(res.stage3_synthesis)
    print("\n" + "=" * 70)
    print("INDIVIDUAL COUNCIL VOICES:")
    for model, op in res.stage1_opinions.items():
        print(f"\n--- [{model}] ---")
        print(op[:300] + ("..." if len(op) > 300 else ""))
