"""
ISHA Agent Nodes — Individual steps in the agentic loop.

Each function takes AgentState in and returns an updated AgentState.
All LLM calls are wrapped so API failures degrade into readable state
messages instead of crashing the graph.
"""

import re
from pathlib import Path

from src.agents.state import AgentState, coerce_state
from src.config import call_coder, call_planner
from src.tools.context_trimmer import trim_traceback
from src.tools.patch_engine import apply_patch
from src.tools.sandbox import make_sandbox, run_tests

_FENCE_RE = re.compile(r"```(?:\w+)?\n(.*?)```", re.S)


def _strip_fences(text: str) -> str:
    """Return the largest fenced block if present, otherwise the raw text."""
    if not text:
        return ""
    blocks = _FENCE_RE.findall(text)
    if blocks:
        return max(blocks, key=len).strip()
    return text.strip()


def _extract_diff(text: str) -> str:
    """Pull a unified diff out of an LLM response."""
    if not text:
        return ""
    cleaned = _strip_fences(text)
    markers = ["diff --git", "--- a/", "--- ", "Index:"]
    starts = [cleaned.find(m) for m in markers if cleaned.find(m) != -1]
    if starts:
        cleaned = cleaned[min(starts):]
    return cleaned.strip()


def _workdir(state: AgentState) -> str:
    """Directory this attempt should operate in (worktree or sandbox copy)."""
    return state.worktree or state.repo_path


def planner_node(state: AgentState) -> AgentState:
    """Generate a structured fix plan from the issue and repo context."""
    state = coerce_state(state)
    prompt = f"""You are an expert software engineer. Given this bug report and
repository context, produce a structured 2-step fix plan:
Step 1: What is the root cause
Step 2: What exact changes to make (file, function, what to change)

BUG REPORT:
{state.issue_text}

REPOSITORY CONTEXT:
{state.repo_context or "(no context provided)"}

REPO PATH: {state.repo_path}
Output the plan only."""
    try:
        plan = call_planner(prompt)
        state.plan = _strip_fences(plan) or "[PLANNER ERROR] empty response"
    except Exception as exc:
        state.plan = f"[PLANNER ERROR] {exc}"
    return state


def regression_test_node(state: AgentState) -> AgentState:
    """Write a failing test that reproduces the bug (red -> green)."""
    state = coerce_state(state)
    prompt = f"""Given this bug report and fix plan, write a pytest test that
REPRODUCES the bug. The test should FAIL right now (red) and
PASS after the fix is applied (green). Output ONLY the test code.

BUG REPORT:
{state.issue_text}

FIX PLAN:
{state.plan}

REPOSITORY CONTEXT:
{state.repo_context or "(no context provided)"}

REPO PATH: {state.repo_path}"""
    try:
        test_code = call_planner(prompt)
        state.regression_test = _strip_fences(test_code)
    except Exception as exc:
        state.regression_test = f"# [REGRESSION TEST ERROR] {exc}"
    return state


def coder_node(state: AgentState) -> AgentState:
    """Generate a unified-diff patch to fix the bug."""
    state = coerce_state(state)
    if "FAILED" in (state.test_output or ""):
        state.retry_count += 1

    retry_hint = ""
    if state.retry_count > 0 and state.test_output:
        retry_hint = (
            "\n\nPREVIOUS ATTEMPT FAILED. The previous patch did not make the tests "
            "pass. Diagnose why and produce a corrected diff.\n"
            "TRIMMED TEST OUTPUT:\n" + trim_traceback(state.test_output)
        )

    prompt = f"""Generate a unified diff patch to fix this bug. Output
ONLY the diff, no explanation. Use standard unified diff format.

BUG REPORT:
{state.issue_text}

FIX PLAN:
{state.plan}

TARGET FILE CONTEXT:
{state.repo_context or "(no context provided)"}

STRATEGY: {state.strategy}
REPO PATH: {state.repo_path}
RETRY INDEX: {state.retry_count}{retry_hint}"""
    try:
        raw = call_coder(prompt)
        patch = _extract_diff(raw)
        state.patch = patch or f"[CODER ERROR] no diff produced: {raw[:300]}"
    except Exception as exc:
        state.patch = f"[CODER ERROR] {exc}"
    return state


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
    # (Phase 6, reset to a clean tree) or a fresh scratch copy.
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

    ok, message = apply_patch(str(target), state.patch)
    if not ok:
        state.test_output = f"FAILED: patch could not be applied — {message}"
        return state

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
    state.test_output = f"{_verdict(output)}\n{output}"
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
