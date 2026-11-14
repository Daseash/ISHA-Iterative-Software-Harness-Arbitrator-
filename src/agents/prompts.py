"""
ISHA Prompt Engineering & Construction — Phase 3/4 context assembly and prompt builders.

Centralizes prompt section budgets, context trimming, localization formatting,
verbatim code snippet injection, and strategy-aware prompt construction for all agent nodes.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from src.agents.state import AgentState
from src.tools.context_trimmer import trim_traceback

_FENCE_RE = re.compile(r"```(?:\w+)?\n(.*?)```", re.S)

_TOOL_MARKUP_RE = re.compile(
    r"<[/]?function_calls>|<invoke\b.*?<[/]invoke>|<parameter\b.*?<[/]parameter>",
    re.S,
)


def _strip_tool_markup(text: str) -> str:
    if not text or "<" not in text:
        return text or ""
    cleaned = text
    for _ in range(3):
        nxt = _TOOL_MARKUP_RE.sub("", cleaned)
        if nxt == cleaned:
            break
        cleaned = nxt
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _bench_mode() -> bool:
    """True when running under the SWE-bench harness (no local test env)."""
    return os.getenv("ISHA_BENCH_MODE", "0") == "1"


def _clip(text: str | None, limit: int) -> str:
    """Bound a context block with graceful truncation and type safety."""
    if limit <= 0:
        return ""
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[context capped at {limit} chars]"


def _clip_issue(text: str | None, limit: int) -> str:
    """P1-01: head+tail clip for issues — traceback tail holds the failing line."""
    text = text or ""
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    head = int(limit * 0.6)
    tail = limit - head
    return text[:head] + f"\n...[clipped {len(text)-limit} chars; tail kept]...\n" + text[-tail:]


# Prompt section budgets
_PLANNER_CONTEXT_CHARS = int(os.getenv("ISHA_PLANNER_CONTEXT_CHARS", "10000"))
_REGRESSION_CONTEXT_CHARS = int(os.getenv("ISHA_REGRESSION_CONTEXT_CHARS", "6000"))
_CODER_CONTEXT_CHARS = int(os.getenv("ISHA_CODER_CONTEXT_CHARS", "4000"))

_ISSUE_CHARS = int(os.getenv("ISHA_ISSUE_CHARS", "6000"))
_PLAN_CHARS = int(os.getenv("ISHA_PLAN_CHARS", "3500"))
_CODE_BLOCK_CHARS = int(os.getenv("ISHA_CODE_BLOCK_CHARS", "8000"))
_HISTORY_CHARS = int(os.getenv("ISHA_HISTORY_CHARS", "800"))
_STYLE_CHARS = int(os.getenv("ISHA_STYLE_CHARS", "600"))
_HINT_CHARS = int(os.getenv("ISHA_HINT_CHARS", "8000"))
_PLANNER_AUX_CHARS = int(os.getenv("ISHA_PLANNER_AUX_CHARS", "5000"))

_TARGETING_FILES = int(os.getenv("ISHA_TARGETING_FILES", "3"))
_TARGETING_SYMBOLS = int(os.getenv("ISHA_TARGETING_SYMBOLS", "4"))


def _strip_fences(text: str) -> str:
    """Return the largest fenced block if present, otherwise the raw text."""
    if not text:
        return ""
    blocks = _FENCE_RE.findall(text)
    if blocks:
        best_block = max(blocks, key=lambda b: len(b))
        return str(best_block).strip()
    return text.strip()


def _unfence(text: str) -> str:
    """Drop the ``` fences but keep everything between them."""
    if not text:
        return ""
    return re.sub(r"^[ \t]*```[^\n]*$", "", text, flags=re.M).strip()


def _extract_diff(text: str) -> str:
    """Pull a unified diff out of an LLM response."""
    if not text:
        return ""
    cleaned = _strip_tool_markup(_strip_fences(text))
    markers = ["diff --git", "--- a/", "--- ", "Index:"]
    starts = [cleaned.find(m) for m in markers if cleaned.find(m) != -1]
    if starts:
        cleaned = cleaned[min(starts):]
    return cleaned.strip()


def localization_section(state: AgentState) -> tuple[str, list]:
    """Ranked file/symbol/line candidates pulled out of the issue text."""
    try:
        from src.tools.localizer import find_test_files, localize

        candidates = localize(state.issue_text, state.repo_path, top_k=6)
    except Exception:
        return "", []
    if not candidates:
        return "", []

    lines = [
        "LOCALIZED SUSPECTS (ranked — issue text parsed for stack traces,",
        "file paths, symbols, snippets; then BM25 + embedding + repo map):",
    ]
    for rank, cand in enumerate(candidates, start=1):
        span = ""
        if cand.line_start:
            span = f" lines {cand.line_start}-{cand.line_end}"
        sym = f" :: {cand.symbol}" if cand.symbol else ""
        lines.append(
            f"  {rank}. {cand.file}{sym}{span}  score={cand.score:.2f} "
            f"[{'; '.join(f'{k}={v:.2f}' for k, v in cand.scores.items())}] "
            f"({cand.reason})"
        )

    tests = find_test_files(
        state.repo_path, [c.file for c in candidates[:3]], top_k=3
    )
    if tests:
        lines.append("EXISTING TESTS MOST LIKELY TO PIN THIS BEHAVIOUR:")
        for path, why in tests:
            lines.append(f"  - {path} ({why})")
    return "\n".join(lines) + "\n", candidates


def code_context_section(state: AgentState, targets: list) -> str:
    """Phase 3: full bodies of suspects + direct callers + relevant tests."""
    if not targets:
        return ""
    normalized = []
    for t in targets:
        if isinstance(t, dict):
            normalized.append({"file": t.get("file", ""), "symbol": t.get("symbol", "")})
        else:
            normalized.append(
                {"file": t.file, "symbol": t.symbol.split("::")[-1] if t.symbol else ""}
            )
    normalized = [t for t in normalized if t["file"]]
    if not normalized:
        return ""

    targeting = ""
    try:
        from src.tools.symbol_target import build_targeting_block, target_file

        ranked: list[dict] = []
        for t in normalized[:_TARGETING_FILES]:
            ranked.extend(target_file(
                state.repo_path, t["file"], state.issue_text or ""
            ))
        ranked.sort(key=lambda r: -r.get("score", 0))
        block = build_targeting_block(ranked[:_TARGETING_SYMBOLS])
        if block:
            targeting = "\n" + block + "\n"
    except Exception:
        targeting = ""

    try:
        from src.tools.codebody import build_coder_context

        block = build_coder_context(state.repo_path, normalized, state.issue_text)
    except Exception:
        return targeting
    if block:
        return targeting + "\n" + block + "\n"
    return targeting


def _prompt_stats(label: str, **sections) -> None:
    """Emit per-section character counts so prompt bloat is measurable."""
    if os.getenv("ISHA_PROMPT_STATS", "0") != "1":
        return
    sizes = {k: len(str(v) if v is not None else "") for k, v in sections.items()}
    parts = ", ".join(f"{k}={n}" for k, n in sizes.items())
    print(f"[prompt] {label}: {sum(sizes.values())} chars ({parts})", file=sys.stderr)


def build_coder_prompt(
    state: AgentState, strategy: str | None = None, extra_hint: str = ""
) -> str:
    """Full coder prompt: issue + plan + Phase-3 code context + guard rails."""
    retry_hint = ""
    if state.retry_count > 0 and state.test_output:
        retry_hint = (
            "\n\nPREVIOUS ATTEMPT FAILED. The previous patch did not make the tests "
            "pass. Diagnose why and produce a corrected diff.\n"
            "TRIMMED TEST OUTPUT:\n" + trim_traceback(state.test_output)
        )
    if state.consistency_warnings:
        warn_str = "\n".join(f"- {w}" for w in state.consistency_warnings)
        retry_hint += f"\n\nCROSS-FILE INCONSISTENCY WARNINGS:\n{warn_str}\nEnsure all callers are updated."
    if state.context_notes:
        notes = "\n".join(f"- {n}" for n in state.context_notes[-8:])
        retry_hint += f"\n\nVALIDATION NOTES:\n{notes}"

    # Verbatim compiler / indentation syntax error handling
    if "STATIC GATE" in (state.test_output or "") or "SyntaxError" in (state.test_output or "") or "IndentationError" in (state.test_output or ""):
        retry_hint += (
            "\n\nCRITICAL COMPILER / INDENTATION SYNTAX ERROR:\n"
            "Your previous patch produced a compiler syntax or indentation error.\n"
            "INSPECT THE VERBATIM CODE LINES IN THE ERROR OUTPUT CAREFULLY.\n"
            "Ensure exact 4-space Python indentation and that all blocks are correctly closed.\n"
        )

    # Targeted traceback guidance for common failure modes
    test_out = state.test_output or ""
    if "TypeError" in test_out:
        retry_hint += (
            "\n\nCRITICAL TYPEERROR DETECTED IN TEST SUITE:\n"
            "- If the error states 'object of type X has no len()', you MUST implement `def __len__(self):` on class X (Class Anchoring).\n"
            "- If the error is 'object of type NoneType has no len()', check `if val is None:` before calling len(val) (Guard Clause Completeness).\n"
            "- Ensure exact return types (do not return None instead of a tuple/list/string or vice versa).\n"
        )
    if "AttributeError" in test_out:
        retry_hint += (
            "\n\nCRITICAL ATTRIBUTEERROR DETECTED IN TEST SUITE:\n"
            "- The test tried to access a missing attribute or method.\n"
            "- Insert the method or property directly into the EXACT target class (Universal Invariant 1: Class Anchoring), NOT an outer helper.\n"
        )
    if "AssertionError" in test_out:
        retry_hint += (
            "\n\nCRITICAL ASSERTIONERROR DETECTED IN TEST SUITE:\n"
            "- The test assertion failed. Review the expected value vs returned value in the traceback above.\n"
            "- Check for off-by-one errors, edge-case conditions, or mathematical formula mismatches.\n"
        )
    if "sympy" in (getattr(state, "instance_id", "") or "").lower() or "sympy" in (getattr(state, "repo_path", "") or "").lower():
        retry_hint += (
            "\n\nSYMPY DOMAIN INVARIANT:\n"
            "- In Python 3.8+, AST node comparisons must preserve Constant vs Name syntax (`ast.Constant(value=False)` vs `ast.Name(id='False')`).\n"
            "- Do not break symbolic expression trees with string manipulation; preserve expression node types.\n"
        )

    apply_failed = (
        any("patch apply failed" in str(n).lower() for n in (state.context_notes or []))
        or "patch could not be applied" in (state.test_output or "").lower()
    )
    if apply_failed:
        retry_hint += (
            "\n\nCRITICAL CONTEXT MISMATCH — PATCH APPLY FAILED:\n"
            "Your previous diff failed to apply because surrounding context lines did not match the file on disk.\n"
            "MANDATORY INSTRUCTIONS FOR THIS RETRY:\n"
            "1. Inspect the TARGET FILE CONTEXT / CODE CONTEXT sections below: these are verbatim lines from the real files.\n"
            "2. In your unified diff, copy all context lines (' ') and removal lines ('-') character-for-character from the context below.\n"
            "3. Do NOT invent, extrapolate, or modify surrounding lines.\n"
            "4. Keep the hunk as minimal as possible (1-5 lines of change)."
        )

    history_section = ""
    try:
        from src.tools.git_history import file_history, mentioned_files

        history = file_history(
            state.repo_path, mentioned_files(state.plan or state.issue_text, limit=3)
        )
        if history:
            history_section = (
                "\nGIT HISTORY (why this code is shaped this way — if it was "
                "changed to fix an earlier bug, do not revert that):\n" + history + "\n"
            )
    except Exception:
        pass

    style_section = ""
    try:
        from src.tools.style_reference import style_examples

        style = style_examples(state.repo_path, state.plan or state.issue_text)
        if style:
            style_section = (
                "\nCODE STYLE REFERENCE (match this file's naming, docstring "
                "and formatting conventions):\n" + style + "\n"
            )
    except Exception:
        pass

    br = state.blast_radius or {}
    blast_line = ""
    if br.get("callers"):
        blast_line = (
            f"\nBLAST RADIUS: ~{br['callers']} callers across {br.get('files', 0)} "
            "files. Keep the diff minimal, additive and signature-compatible.\n"
        )

    code_block = code_context_section(state, state.localization)
    if not code_block and state.repo_path:
        try:
            from src.tools.git_history import mentioned_files
            from src.tools.codebody import full_bodies

            m_files = mentioned_files(state.plan or state.issue_text or "", limit=3)
            fb_chunks = []
            for mf in m_files:
                fb = full_bodies(state.repo_path, mf, budget=8000)
                if fb:
                    fb_chunks.append(fb)
            if fb_chunks:
                code_block = "CODE CONTEXT (verbatim files from repository):\n\n" + "\n\n".join(fb_chunks)
        except Exception:
            pass

    loc_line = ""
    if state.localization:
        top = state.localization[0]
        loc_line = (
            f"\nBEST LOCALIZATION: {top.get('file')}"
            + (f" :: {top.get('symbol')}" if top.get("symbol") else "")
            + " — start there; do not wander into unrelated files.\n"
        )

    issue = _clip_issue(state.issue_text, _ISSUE_CHARS)
    plan = _clip(state.plan, _PLAN_CHARS)
    code_block = _clip(code_block, _CODE_BLOCK_CHARS)
    history_section = _clip(history_section, _HISTORY_CHARS)
    style_section = _clip(style_section, _STYLE_CHARS)
    retry_hint = _clip(retry_hint, _HINT_CHARS)
    extra_hint = _clip(extra_hint, _HINT_CHARS)
    extra_hint_sep = "\n" if retry_hint and extra_hint else ""

    from src.memory.store import get_episodic_invariants, org_of

    org = org_of(getattr(state, "instance_id", "") or "", getattr(state, "repo_path", "") or "")
    episodic_rules = get_episodic_invariants(org)
    episodic_section = ""
    if episodic_rules:
        episodic_lines = "\n".join(f"- {r}" for r in episodic_rules)
        episodic_section = f"\nEPISODIC DOMAIN PLAYBOOKS (dynamically loaded from memory.db for '{org}'):\n{episodic_lines}\n"

    _prompt_stats("coder", issue=issue, plan=plan,
                  repo=_clip(state.repo_context, _CODER_CONTEXT_CHARS),
                  code=code_block, history=history_section, style=style_section,
                  retry=retry_hint, extra=extra_hint, loc=loc_line, fixed=260)

    return f"""Generate a unified diff patch to fix this bug. Output
ONLY the diff, no explanation. Use standard unified diff format
(--- a/path  +++ b/path  @@ hunk headers).

MINIMAL DIFF RULES (non-negotiable — SENIOR INVARIANT MODE):
- Change only what the fix requires. No refactors, no renames, no
  reformatting, no comment/docstring edits, no unrelated cleanups.
- Does standard library or existing helper in this codebase already do this? Reuse it.
- Can it be one line? Make it one line. Minimal diff wins.
- Bug fix = root cause, not symptom. Fix where all callers route through.
- Do not touch test files unless the fix itself requires it.
- Keep the diff inside the localized files unless the bug is provably cross-file.
- CLASS ANCHORING: Insert methods/properties into the EXACT enclosing class (e.g. class SimpleLazyObject, class ModelAdmin), NEVER an earlier class or helper.
- GUARD CLAUSE COMPLETENESS: Check `if val is None:` before accessing attributes or calling `len(val)`. Calling `len(None)` raises `TypeError`. Always guard against `None`, empty containers, or missing keys before slicing or querying.
- DECORATOR PRESERVATION: When wrapping callables or modifying decorators (`functools.partial`), wrap with `functools.wraps(...)` to preserve function introspection (`__name__`, `__doc__`, `__wrapped__`).
- EXECUTION SCOPE & NAMESPACES: In dynamic code execution (`exec`, `eval`), always provide an explicit global namespace with {{'__name__': '__main__'}} so top-level imports and closures resolve properly.
- TYPE & RETURN INVARIANTS: Strictly preserve exact return types and falsy distinctions (None vs '' vs 0 vs False). Do not coerce None to '' or drop empty strings unless explicitly required.
- SIGNATURE SAFETY: When modifying methods, preserve caller compatibility (*args, **kwargs).
- CALLABLE RESOLUTION: If an attribute or parameter can be a callable or PathLike, handle it safely.{episodic_section}
- The TARGET FILE CONTEXT / CODE CONTEXT sections below are verbatim
  excerpts of the real files. Copy every context and removal line from them
  character-for-character. If a line you want to change is not shown, do not
  invent it — change only what is visible, using exact line numbers.

BUG REPORT:
{issue}

FIX PLAN:
{plan}
{loc_line}
TARGET FILE CONTEXT:
{_clip(state.repo_context, _CODER_CONTEXT_CHARS)}
{code_block}
{history_section}{style_section}{blast_line}
STRATEGY: {strategy or state.strategy}
REPO PATH: {state.repo_path}
RETRY INDEX: {state.retry_count}{retry_hint}{extra_hint_sep}{extra_hint}"""
