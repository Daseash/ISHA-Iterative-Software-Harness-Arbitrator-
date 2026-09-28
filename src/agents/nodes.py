"""
ISHA Agent Nodes — Individual steps in the agentic loop.

Each function takes AgentState in and returns an updated AgentState.
All LLM calls are wrapped so API failures degrade into readable state
messages instead of crashing the graph.
"""

import os
import re
import sys
from pathlib import Path

from src.agents.state import AgentState, coerce_state
from src.config import call_coder, call_planner, get_model_log
from src.tools.context_trimmer import trim_traceback
from src.tools.patch_engine import apply_patch
from src.tools.sandbox import make_sandbox, run_tests

_FENCE_RE = re.compile(r"```(?:\w+)?\n(.*?)```", re.S)

# Models trained on tool-calling emit <function_calls>/<invoke>/<parameter>
# markup when they want to read a file. We cannot serve those tool calls from
# a single completion, so the markup is stripped and the prose kept - without
# this the plan is unusable and the confidence line never parses.
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


def _clip(text: str, limit: int) -> str:
    """Bound a context block.

    Free-tier TPM windows are the binding constraint on a benchmark run, so
    every context section is budgeted explicitly rather than truncated
    mid-hunk by a character limit much further downstream.
    """
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[context capped at {limit} chars]"


_PLANNER_CONTEXT_CHARS = int(os.getenv("ISHA_PLANNER_CONTEXT_CHARS", "5000"))
_REGRESSION_CONTEXT_CHARS = int(os.getenv("ISHA_REGRESSION_CONTEXT_CHARS", "3500"))
_CODER_CONTEXT_CHARS = int(os.getenv("ISHA_CODER_CONTEXT_CHARS", "900"))

# Per-section budgets for the coder prompt.  Free-tier Groq TPM is measured
# in tokens; a 34k-char prompt alone exceeds a typical window, so every
# section is capped before assembly and reported by ``_prompt_stats``.
_ISSUE_CHARS = int(os.getenv("ISHA_ISSUE_CHARS", "3000"))
_PLAN_CHARS = int(os.getenv("ISHA_PLAN_CHARS", "2000"))
_CODE_BLOCK_CHARS = int(os.getenv("ISHA_CODE_BLOCK_CHARS", "5100"))
_HISTORY_CHARS = int(os.getenv("ISHA_HISTORY_CHARS", "800"))
_STYLE_CHARS = int(os.getenv("ISHA_STYLE_CHARS", "600"))
_HINT_CHARS = int(os.getenv("ISHA_HINT_CHARS", "4000"))
_PLANNER_AUX_CHARS = int(os.getenv("ISHA_PLANNER_AUX_CHARS", "2500"))


def _strip_fences(text: str) -> str:
    """Return the largest fenced block if present, otherwise the raw text."""
    if not text:
        return ""
    blocks = _FENCE_RE.findall(text)
    if blocks:
        return max(blocks, key=len).strip()
    return text.strip()


def _unfence(text: str) -> str:
    """Drop the ``` fences but keep *everything* between them.

    For prose outputs (the fix plan) keeping only the largest block would throw
    the plan away and hand the coder a bare code fragment — which is exactly
    what happened on most instances before this existed.
    """
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


def _workdir(state: AgentState) -> str:
    """Directory this attempt should operate in (worktree or sandbox copy)."""
    return state.worktree or state.repo_path


# ── Phase 2/3 context helpers ──────────────────────────────────────────────

def localization_section(state: AgentState) -> tuple[str, list]:
    """Ranked file/symbol/line candidates pulled out of the issue text.

    Returns (prompt block, candidate dicts). The candidate list is also what
    the Coder's full-body context is built from, so localization and context
    construction can never disagree about where the bug lives.
    """
    try:
        from src.tools.localizer import find_test_files, localize

        candidates = localize(state.issue_text, state.repo_path, top_k=6)
    except Exception:
        return "", []
    if not candidates:
        return "", []

    lines = ["LOCALIZED SUSPECTS (ranked — issue text parsed for stack traces,",
             "file paths, symbols, snippets; then BM25 + embedding + repo map):"]
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
    """Phase 3: full bodies of suspects + direct callers + relevant tests.

    ``targets`` accepts localizer ``Candidate`` objects or the plain dicts
    stored on ``state.localization``.
    """
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
    try:
        from src.tools.codebody import build_coder_context

        block = build_coder_context(state.repo_path, normalized, state.issue_text)
    except Exception:
        return ""
    if block:
        return "\n" + block + "\n"
    return ""


def planner_node(state: AgentState) -> AgentState:
    """Generate a structured fix plan from the issue and repo context."""
    state = coerce_state(state)

    # Phase 2 — seeds parsed out of the issue text drive file -> symbol ->
    # line localization; the ranked list is stored so the Coder builds its
    # full-body context from exactly the same places the plan referenced.
    loc_section, candidates = localization_section(state)
    if candidates:
        state.localization = [c.as_dict() for c in candidates]

    # Learn from this repo's own fix history (retrieved from the fix ledger).
    history_section = ""
    try:
        from src.agents.fix_history import render_hits, retrieve_fixes

        hits = retrieve_fixes(state.issue_text, state.repo_path)
        if hits:
            history_section = (
                "\nSIMILAR PAST FIXES IN THIS REPO (reuse what worked, "
                "don't repeat what failed):\n" + render_hits(hits) + "\n"
            )
    except Exception:
        pass

    # Blast-radius caution (caller fan-out computed during investigation).
    br = state.blast_radius or {}
    blast_line = ""
    if br.get("callers") or br.get("score"):
        blast_line = (
            f"\nBLAST RADIUS: ~{br.get('callers', 0)} callers across "
            f"{br.get('files', 0)} files (score {br.get('score', 0):.2f}). "
            "If fan-out is high, prefer the smallest change that fixes the "
            "bug; do not change public signatures unless unavoidable.\n"
        )

    # Test file summaries — so the plan accounts for existing test expectations.
    test_section = ""
    try:
        from src.tools.dependency_graph import DependencyGraph

        dep_graph = DependencyGraph(state.repo_path)
        tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", state.issue_text))
        entry_pts = [s.name for s in dep_graph.definitions if s.name in tokens][:10]
        if not entry_pts:
            entry_pts = [t for t in tokens if len(t) > 3][:5]
        impact = dep_graph.analyze_impact(entry_pts)
        test_contents = []
        for tf in impact.impacted_test_files[:2]:
            tpath = Path(state.repo_path) / tf
            if tpath.is_file():
                try:
                    content = tpath.read_text(encoding="utf-8", errors="replace")
                    test_contents.append(f"# {tf}\n{content[:1200]}")
                except Exception:
                    pass
        if test_contents:
            test_section = (
                "\nEXISTING TEST FILES (account for these test expectations):\n"
                + "\n\n".join(test_contents) + "\n"
            )
    except Exception:
        pass

    prompt = f"""You are an expert software engineer. Given this bug report and
repository context, produce a structured 2-step fix plan:
Step 1: What is the root cause
Step 2: What exact changes to make (file, function, what to change)

You have NO tools: do not emit <function_calls> or <invoke> markup, do not
ask to read files. Everything you need is already in this prompt - answer
directly in prose.

IMPORTANT: If the bug spans multiple files (e.g. a function signature
mismatch between a definition and its callers), list ALL files that must
be changed.  The patch must be atomic — fixing only one file and leaving
its callers broken is not acceptable.

BUG REPORT:
{_clip(state.issue_text, _ISSUE_CHARS)}

REPOSITORY CONTEXT:
{_clip(state.repo_context, _PLANNER_CONTEXT_CHARS)}
{_clip(loc_section + history_section + test_section, _PLANNER_AUX_CHARS)}{blast_line}
REPO PATH: {state.repo_path}
Output the plan only, then finish with exactly one final line in this format:
CONFIDENCE: <0.00-1.00>
Score how completely you understand the root cause from the information
given. Use the full range: report below 0.40 only when the report lacks
reproduction details or the relevant code is not visible in the context."""
    _prompt_stats("planner", prompt=prompt)
    try:
        plan_raw = call_planner(prompt)
        plan = _strip_tool_markup(_strip_fences(plan_raw)) or "[PLANNER ERROR] empty response"
        conf = re.search(r"CONFIDENCE:\s*([0-9]*\.?[0-9]+)", plan)
        if conf:
            try:
                state.planner_confidence = max(0.0, min(1.0, float(conf.group(1))))
            except ValueError:
                state.planner_confidence = -1.0
            plan = re.sub(r"^\s*CONFIDENCE:.*$", "", plan, flags=re.M).strip()
        else:
            state.planner_confidence = -1.0
        state.plan = plan
    except Exception as exc:
        state.plan = f"[PLANNER ERROR] {exc}"
        state.planner_confidence = -1.0
    state.model_log = get_model_log()
    return state


def confidence_gate_node(state: AgentState) -> AgentState:
    """Escalate to a human when the planner doesn't understand the bug well enough.

    A senior dev says "this ticket needs more info" instead of guessing;
    this node is that instinct. Sets `escalation`, which routes the run to
    the approval/checkpoint path before any patch is attempted.
    """
    state = coerce_state(state)
    try:
        threshold = float(os.getenv("ISHA_CONFIDENCE_THRESHOLD", "0.4"))
    except ValueError:
        threshold = 0.4
    confidence = state.planner_confidence
    if 0.0 <= confidence < threshold:
        state.escalation = (
            f"low planner confidence {confidence:.2f} < {threshold:.2f}: "
            "the bug is not understood well enough to patch safely"
        )
    return state


def regression_test_node(state: AgentState) -> AgentState:
    """Write failing tests that reproduce the bug, plus edge cases (red -> green)."""
    state = coerce_state(state)
    prompt = f"""Given this bug report and fix plan, write a pytest test module that
REPRODUCES the bug. The first test must FAIL right now (red) and PASS after
the fix is applied (green).

Beyond the minimal reproduction, add 2-3 edge-case tests a senior engineer
would write: boundary values, empty/zero/None input, invalid input raising
the documented error, or the numeric edge of the reported bug (negatives,
overflow, duplicates, case sensitivity). Only include edge cases the fix
plan guarantees will pass after the fix — no speculative behavior changes.

Output ONLY the test code (multiple test functions allowed).

BUG REPORT:
{_clip(state.issue_text, _ISSUE_CHARS)}

FIX PLAN:
{_clip(state.plan, _PLAN_CHARS)}

REPOSITORY CONTEXT:
{_clip(state.repo_context, _REGRESSION_CONTEXT_CHARS)}

REPO PATH: {state.repo_path}"""
    _prompt_stats("regression", prompt=prompt)
    try:
        test_code = call_planner(prompt)
        state.regression_test = _strip_tool_markup(_strip_fences(test_code))
    except Exception as exc:
        state.regression_test = f"# [REGRESSION TEST ERROR] {exc}"
    state.model_log = get_model_log()
    return state


def build_coder_prompt(state: AgentState, strategy: str | None = None,
                       extra_hint: str = "") -> str:
    """Full coder prompt: issue + plan + Phase-3 code context + guard rails.

    Kept as a module-level function so candidate generation can vary only the
    strategy / temperature instead of drifting away from what the graph uses.
    """
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

    # Git history of the files the plan touches — don't undo past bugfixes.
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

    # Style reference from the target file — match the codebase's conventions.
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

    # Blast-radius caution — high fan-out code gets the smallest safe diff.
    br = state.blast_radius or {}
    blast_line = ""
    if br.get("callers"):
        blast_line = (
            f"\nBLAST RADIUS: ~{br['callers']} callers across {br.get('files', 0)} "
            "files. Keep the diff minimal, additive and signature-compatible.\n"
        )

    # Phase 3 — full bodies of the suspect symbols, their callers, the tests.
    code_block = code_context_section(state, state.localization)

    loc_line = ""
    if state.localization:
        top = state.localization[0]
        loc_line = (
            f"\nBEST LOCALIZATION: {top.get('file')}"
            + (f" :: {top.get('symbol')}" if top.get("symbol") else "")
            + " — start there; do not wander into unrelated files.\n"
        )

    issue = _clip(state.issue_text, _ISSUE_CHARS)
    plan = _clip(state.plan, _PLAN_CHARS)
    code_block = _clip(code_block, _CODE_BLOCK_CHARS)
    history_section = _clip(history_section, _HISTORY_CHARS)
    style_section = _clip(style_section, _STYLE_CHARS)
    retry_hint = _clip(retry_hint, _HINT_CHARS)
    extra_hint = _clip(extra_hint, _HINT_CHARS)
    _prompt_stats("coder", issue=issue, plan=plan,
                  repo=_clip(state.repo_context, _CODER_CONTEXT_CHARS),
                  code=code_block, history=history_section, style=style_section,
                  retry=retry_hint, extra=extra_hint, loc=loc_line, fixed=260)

    return f"""Generate a unified diff patch to fix this bug. Output
ONLY the diff, no explanation. Use standard unified diff format
(--- a/path  +++ b/path  @@ hunk headers).

MINIMAL DIFF RULES (non-negotiable):
- Change only what the fix requires. No refactors, no renames, no
  reformatting, no comment/docstring edits, no unrelated cleanups.
- Do not touch test files unless the fix itself requires it.
- Keep the diff inside the localized files unless the bug is provably
  cross-file.
- Every call site of a changed signature must be updated in the SAME diff.
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
RETRY INDEX: {state.retry_count}{retry_hint}{extra_hint}"""


def _prompt_stats(label: str, **sections) -> None:
    """Emit per-section character counts so prompt bloat is measurable."""
    if os.getenv("ISHA_PROMPT_STATS", "0") != "1":
        return
    sizes = {k: len(str(v) if v is not None else "") for k, v in sections.items()}
    parts = ", ".join(f"{k}={n}" for k, n in sizes.items())
    print(f"[prompt] {label}: {sum(sizes.values())} chars ({parts})", file=sys.stderr)


def coder_node(state: AgentState) -> AgentState:
    """Generate a unified-diff patch to fix the bug."""
    state = coerce_state(state)
    if "FAILED" in (state.test_output or ""):
        state.retry_count += 1

    prompt = build_coder_prompt(state)
    try:
        raw = call_coder(prompt)
        patch = _extract_diff(raw)
        state.patch = patch or f"[CODER ERROR] no diff produced: {raw[:300]}"
    except Exception as exc:
        state.patch = f"[CODER ERROR] {exc}"
    state.model_log = get_model_log()
    return state


def candidate_node(state: AgentState) -> AgentState:
    """Phase 4/5/6 — N candidates, verified, then one selected.

    Bench-mode only, and only when ``ISHA_CANDIDATES > 1``; with N = 1 the
    node is a no-op so the single-candidate path stays byte-identical to the
    baseline system.
    """
    state = coerce_state(state)
    if not _bench_mode() or not state.patch or state.patch.startswith("["):
        return state
    try:
        n = int(os.getenv("ISHA_CANDIDATES", "1"))
    except ValueError:
        n = 1
    if n <= 1:
        return state

    from src.agents.candidates import (
        cleanup_candidates,
        generate_candidates,
        rank_candidates,
    )

    instance_id = state.instance_id or Path(state.repo_path).name

    def _log(payload: dict) -> None:
        """Surface repair attempts as coder-visible notes for a later retry."""
        detail = payload.get("error") or "; ".join(payload.get("errors") or [])
        note = f"candidate {payload.get('candidate')}: {payload.get('event')} {detail}"
        state.context_notes = list(state.context_notes) + [note.strip()[:300]]

    candidates = generate_candidates(
        state,
        n=n,
        instance_id=instance_id,
        seed_patch=state.patch,
        log=_log,
    )
    if not candidates:
        return state

    # ── LAYA scoring (local, cheap) ─────────────────────────────────────
    judge = None
    try:
        from src.review.laya_judge import get_judge

        judge = get_judge()
    except Exception:
        judge = None

    for cand in candidates:
        if not cand.patch:
            continue
        if judge is None:
            continue
        try:
            scores = judge.score_patch(state.issue_text, state.plan, cand.patch)
            dangers = judge.check_dangers(cand.patch)
            cand.laya = {**scores, **dangers}
            cand.laya_combined = float(scores.get("composite", 0.0))
        except Exception as exc:
            cand.laya = {"error": str(exc)[:200]}

    # ── Repro verification in the official image (Phase 5) ──────────────
    verify_on = os.getenv("ISHA_VERIFY", "1") != "0"
    if verify_on:
        try:
            _verify_candidates(state, candidates)
        except Exception as exc:
            for cand in candidates:
                cand.repro = {"available": False, "reason": f"verifier error: {exc}"}

    # ── Score, rank, select ─────────────────────────────────────────────
    from src.review import calibration

    model = calibration.load()
    for cand in candidates:
        feats = calibration.features_for(
            cand.laya, cand.gate_ok, cand.repro, cand.diff_size, len(cand.changed)
        )
        outcome = calibration.combine(feats, model)
        cand.combined_score = float(outcome["score"])
        cand.rank_reason = outcome["mode"]

    ordered = rank_candidates(candidates)
    winner = ordered[0] if ordered else None

    state.candidates = [c.as_dict() for c in ordered]
    if winner and winner.valid:
        state.patch = winner.patch
        state.strategy = winner.strategy
        state.laya_scores = {**winner.laya, "combined": winner.combined_score,
                             "mode": winner.rank_reason}
        state.selected_candidate = {
            **winner.as_dict(),
            "beat": len([c for c in ordered if c is not winner]),
        }
    elif winner:
        state.selected_candidate = winner.as_dict()
        state.context_notes = list(state.context_notes) + [
            "candidate_node: no candidate passed the gates; keeping coder patch"
        ]

    cleanup_candidates(candidates, state.repo_path)
    state.model_log = get_model_log()
    return state


def _verify_candidates(state: AgentState, candidates) -> None:
    """Run the repro test inside the instance image for each valid candidate."""
    from src.bench import verify as vfy

    valid = [c for c in candidates if c.valid and c.patch]
    if not valid:
        return

    record = None
    try:
        from src.bench.dataset import load_records

        wanted = state.instance_id
        record = next((r for r in load_records() if r["instance_id"] == wanted), None)
    except Exception:
        record = None
    if not record or not record.get("image"):
        for cand in candidates:
            cand.repro = {"available": False, "reason": "instance record has no image"}
        return

    ready, why = vfy.docker_ready()
    if not ready:
        for cand in candidates:
            cand.repro = {"available": False, "reason": f"docker unavailable: {why}"}
        return

    meta = vfy.instance_meta(record)
    if not vfy.image_available(meta["image"]):
        vfy.pull_image(meta["image"])
    if not vfy.image_available(meta["image"]):
        for cand in candidates:
            cand.repro = {"available": False,
                          "reason": f"image unavailable: {meta['image']}"}
        return

    try:
        touched = vfy.touched_targets(record, valid[0].changed, state.repo_path)
    except Exception:
        touched = []

    max_verify = int(os.getenv("ISHA_VERIFY_MAX", "3"))
    for cand in valid[:max(1, max_verify)]:
        cand.repro = vfy.verify_instance(
            record,
            state.regression_test,
            cand.patch,
            touched_targets=touched,
        )


def sandbox_node(state: AgentState) -> AgentState:
    """Run tests against the candidate patch in an isolated copy."""
    state = coerce_state(state)
    if not state.repo_path:
        state.test_output = "FAILED: no repo_path set"
        return state
    if not state.patch or state.patch.startswith("[CODER ERROR]"):
        state.test_output = "FAILED: no patch to apply"
        return state

    repo = Path(state.repo_path)
    if not repo.exists():
        state.test_output = f"FAILED: repo path missing: {state.repo_path}"
        return state

    # Each attempt works on its own isolated directory: a git worktree
    # or a fresh scratch copy.
    if state.worktree:
        target = Path(state.worktree)
        if not target.exists():
            state.test_output = f"FAILED: worktree missing: {state.worktree}"
            return state
        if (target / ".git").exists():
            import subprocess

            subprocess.run(
                ["git", "checkout", "--", "."],
                cwd=str(target),
                capture_output=True,
            )
        else:
            from src.tools.sandbox import copy_repo

            copy_repo(str(repo), str(target))
    else:
        state.worktree = make_sandbox(str(repo))
        target = Path(state.worktree)

    # 1. Cross-file consistency checks
    from src.tools.consistency_checker import check_patch_consistency

    warnings = check_patch_consistency(str(target), state.patch)
    state.consistency_warnings = warnings

    # 2. Apply patch
    ok, message = apply_patch(str(target), state.patch)
    if not ok:
        state.context_notes = list(state.context_notes) + [
            f"patch apply failed: {message[:300]}"
        ]
        state.test_output = f"FAILED: patch could not be applied — {message}"
        return state

    # 2b. Bench mode: the host has no environment for these repos (and the
    #     official harness is the ground truth), so gate on static validity
    #     instead of a local pytest run.  Apply errors and syntax errors
    #     still fail loudly and feed straight back into the retry loop.
    if _bench_mode():
        from src.bench.gates import compile_gate

        gate = compile_gate(str(target), state.patch, baseline_repo=state.repo_path)
        if not gate.ok:
            state.context_notes = list(state.context_notes) + [
                f"static gate rejected the patch: {e}" for e in gate.errors[:5]
            ]
            state.test_output = "FAILED: STATIC GATE — " + "; ".join(gate.errors[:6])
            return state
        state.test_output = (
            "PASSED\n[bench mode] patch applies and passes ast/py_compile/"
            "pyflakes gates; dynamic tests are executed by the official "
            "SWE-bench harness."
        )
        state.full_test_output = ""
        return state

    # 3. Write and run regression test
    test_file = None
    if state.regression_test and not state.regression_test.startswith("#"):
        try:
            (target / "test_regression_isha.py").write_text(
                _strip_fences(state.regression_test), encoding="utf-8"
            )
            test_file = "test_regression_isha.py"
        except OSError:
            pass

    output = run_tests(str(target), test_file=test_file)
    if not output:
        output = "sandbox produced no output"

    verdict = _verdict(output)

    # 4. If regression test passes, run full repo test suite to catch collateral breakage.
    # Only flag as regression if NEW failures are introduced that were NOT already failing in baseline.
    if verdict == "PASSED":
        full_output = run_tests(str(target), test_file=None)
        state.full_test_output = full_output
        baseline = state.investigation_report or ""

        # Extract failed test identifiers
        curr_failed = set(re.findall(r"FAILED\s+([^\s]+)", full_output))
        base_failed = set(re.findall(r"FAILED\s+([^\s]+)", baseline))

        # True regressions are tests that failed now but were NOT failing at baseline
        new_regressions = curr_failed - base_failed
        if new_regressions:
            reg_list = "\n".join(f"- {f}" for f in sorted(new_regressions))
            state.test_output = (
                f"FAILED: Collateral regression detected! New test passed, but previously working tests broke:\n"
                f"{reg_list}\n\nFull pytest output:\n{full_output}"
            )
            return state

    state.test_output = f"{verdict}\n{output}"
    return state


def _verdict(output: str) -> str:
    """Turn raw pytest output into a PASSED/FAILED marker for the graph."""
    if re.search(r"\b\d+\s+failed\b", output):
        return "FAILED"
    if re.search(r"\b\d+\s+passed\b", output):
        return "PASSED"
    if output.startswith("FAILED") or "Traceback" in output or "error" in output.lower():
        return "FAILED"
    return "FAILED"
