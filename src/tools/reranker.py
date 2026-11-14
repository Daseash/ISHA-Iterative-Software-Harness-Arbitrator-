"""
ISHA Reranker & Test Discovery — Post-retrieval cross-encoder and LLM re-ranking.

Provides:
- specialist_rerank: Local INT8 ONNX cross-encoder re-ranking.
- llm_rerank: Structured LLM-guided file candidate re-ranking.
- find_test_files: Discover existing repository tests pinning down suspect behaviors.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple

from src.ingestion.parser import SKIP_DIRS

if TYPE_CHECKING:
    from src.tools.localizer import Candidate

_SPECIALIST_SUITE = None


def _local_rerank_enabled() -> bool:
    """Node 1 is explicit opt-in."""
    if os.getenv("ISHA_FORCE_OFFLINE") == "1":
        return False
    return os.getenv("ISHA_LOCAL_RERANK", "0").strip() == "1"


def specialist_rerank(
    issue_text: str,
    candidates: list[Candidate],
    top_n: int = 8,
) -> list[Candidate]:
    """Node 1: reorder the top candidates with the local INT8 cross-encoder."""
    if len(candidates) <= 1 or not _local_rerank_enabled():
        return candidates

    global _SPECIALIST_SUITE
    try:
        if _SPECIALIST_SUITE is None:
            from src.models.specialist_onnx import ISHASpecialistSuite

            _SPECIALIST_SUITE = ISHASpecialistSuite()
        pool = candidates[:top_n]
        payload = [
            {
                "path": c.file,
                "ast_summary": " ".join(c.symbols[:8]) or c.symbol,
                "normalized_rag_score": c.score,
            }
            for c in pool
        ]
        ranked = _SPECIALIST_SUITE.rerank_files(
            issue_text, payload, top_k=len(payload)
        )
        by_file = {c.file: c for c in pool}
        out: list[Candidate] = []
        for item in ranked:
            cand = by_file.get(item["path"])
            if cand is None:
                continue
            prob = float(item.get("rerank_prob", 0.0))
            cand.scores["local_rerank"] = prob
            cand.reason = (
                f"local_rerank p={prob:.3f}" + (f" | {cand.reason}" if cand.reason else "")
            )
            out.append(cand)
        seen = {c.file for c in out}
        out.extend(c for c in candidates if c.file not in seen)
        return out
    except Exception as exc:
        print(
            f"[localizer] local rerank unavailable ({exc.__class__.__name__}: {exc}) "
            "— keeping retrieval order",
            file=sys.stderr,
        )
        return candidates


def llm_rerank(
    issue_text: str,
    candidates: list[Candidate],
    top_n: int = 8,
) -> list[Candidate]:
    """Re-rank top candidates using a cheap, structured LLM call."""
    if not candidates or len(candidates) <= 1:
        return candidates

    pool = candidates[:top_n]
    rest = candidates[top_n:]

    # Fast short-circuit: if the top candidate is already uniquely strong from stack traces
    if pool[0].scores.get("seed", 0) >= 0.9 and (len(pool) == 1 or pool[1].scores.get("seed", 0) < 0.5):
        return candidates

    cand_lines = []
    for i, c in enumerate(pool, 1):
        sym_desc = f" (symbol: {c.symbol}, lines {c.line_start}-{c.line_end})" if c.symbol else ""
        cand_lines.append(f"{i}. {c.file}{sym_desc}")

    _issue_head, _issue_tail = issue_text[:1200], issue_text[-600:]
    _issue_snip = _issue_head if len(issue_text) <= 1800 else _issue_head + "\n...[clipped]...\n" + _issue_tail
    prompt = (
        "You are an expert software engineer localizing a bug in a codebase.\n"
        "Given the bug report and candidate files retrieved from the codebase, "
        "re-rank the candidates so that the file most likely to contain the actual defect "
        "(root cause code that must be edited) appears first.\n"
        "Exclude tests, docs, and example files unless the bug specifically targets them.\n\n"
        f"BUG REPORT:\n{_issue_snip}\n\n"
        f"CANDIDATES:\n" + "\n".join(cand_lines) + "\n\n"
        "Return ONLY a JSON array of the candidate file paths in ranked order, from most likely to least likely:\n"
        '["path/to/file1.py", "path/to/file2.py", ...]'
    )

    try:
        from src.config import OFFLINE_MODE, call_planner
        if OFFLINE_MODE:
            return candidates

        reply = call_planner(prompt)
        if not reply:
            print("[localizer] rerank empty reply — keeping retrieval order", file=sys.stderr)
            return candidates

        import json
        cleaned = re.sub(r"^```(?:json)?\s*", "", reply.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```\s*$", "", cleaned.strip(), flags=re.MULTILINE).strip()
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        order = json.loads(cleaned)
        if isinstance(order, list) and order:
            by_file = {c.file: c for c in pool}
            reranked = []
            seen = set()
            for path_str in order:
                target_str = str(path_str).replace("\\", "/").strip()
                cand = by_file.get(target_str)
                if not cand:
                    for f, c in by_file.items():
                        if f.endswith(target_str) or target_str.endswith(f):
                            cand = c
                            break
                if cand and cand.file not in seen:
                    seen.add(cand.file)
                    cand.reason = f"llm_rerank #{len(reranked)+1} ({cand.reason})"
                    reranked.append(cand)
            for c in pool:
                if c.file not in seen:
                    reranked.append(c)
            return reranked + rest
    except Exception as exc:
        print(f"[localizer] rerank failed ({exc.__class__.__name__}) — keeping retrieval order", file=sys.stderr)
        return candidates
    print("[localizer] rerank unparseable — keeping retrieval order", file=sys.stderr)
    return candidates


_TEST_FILES_CACHE: dict[str, list[str]] = {}


def find_test_files(
    repo_path: str, target_files: list[str], top_k: int = 4
) -> list[tuple[str, str]]:
    """Most relevant existing test files for the suspect source files."""
    root = Path(repo_path)
    cache_key = str(root)
    if cache_key in _TEST_FILES_CACHE:
        all_tests = _TEST_FILES_CACHE[cache_key]
    else:
        all_tests = []
        for path in root.rglob("*.py"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            try:
                rel = str(path.relative_to(root)).replace("\\", "/")
            except ValueError:
                continue
            name = path.name.lower()
            parts = [p.lower() for p in rel.split("/")]
            if name.startswith("test_") or name.endswith("_test.py") or "tests" in parts[:-1]:
                all_tests.append(rel)
        _TEST_FILES_CACHE[cache_key] = all_tests

    scored: list[tuple[int, str, str]] = []
    for target in target_files:
        tail = Path(target).name
        stem = tail[:-3] if tail.endswith(".py") else tail
        candidates = stem.replace("test_", "").replace("_test", "")
        for test in all_tests:
            score, why = 0, ""
            tname = Path(test).name.lower()
            if stem and (stem.lower().replace("test_", "") in tname or tname.replace("test_", "") in stem.lower()):
                score, why = 3, f"module name matches {tail}"
            elif any(part in test.lower() for part in Path(target).parts[:-1]):
                score, why = 2, "same package as " + tail
            if candidates and candidates.lower() in test.lower():
                score = max(score, 2)
                why = why or f"exercises {stem}"
            if score:
                scored.append((score, test, why))

    scored.sort(key=lambda t: (-t[0], t[1]))
    out: list[tuple[str, str]] = []
    for _, test, why in scored:
        if (test, why) not in out:
            out.append((test, why))
        if len(out) >= top_k:
            break
    return out
