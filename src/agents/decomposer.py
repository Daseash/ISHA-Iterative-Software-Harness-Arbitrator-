"""
ISHA Hierarchical Bug Decomposer.

Decomposes large, multi-file, or complex bugs into an ordered sequence of
atomic, independently verifiable sub-issues. Each sub-issue is processed
sequentially through ISHA's core loop, with cumulative patches passing
as context to subsequent steps.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.agents.state import AgentState, coerce_state
from src.config import LLM_ENABLED, call_planner


class SubIssue(BaseModel):
    """An atomic, independently fixable sub-component of a larger bug."""
    id: int
    title: str
    description: str
    target_files: List[str] = Field(default_factory=list)
    status: str = "pending"  # pending | in_progress | resolved | failed
    patch: str = ""


def _parse_sub_issues_json(raw_text: str) -> List[SubIssue]:
    """Extract and validate JSON list of sub-issues from model output."""
    # P1-02: non-greedy (was greedy \[.*\] swallowing trailing text into invalid JSON).
    match = re.search(r"\[.*?\]", raw_text, re.DOTALL)
    candidates = [match.group(0)] if match else []
    # Also try largest valid array as fallback
    greedy = re.search(r"\[.*\]", raw_text, re.DOTALL)
    if greedy and (not candidates or greedy.group(0) != candidates[0]):
        candidates.append(greedy.group(0))
    for raw in candidates:
        try:
            data = json.loads(raw)
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        sub_issues = []
        for item in data:
            # P1-02: per-item validation (was one bad item discarding all).
            try:
                if not isinstance(item, dict):
                    continue
                sub_issues.append(
                    SubIssue(
                        id=int(item.get("id", len(sub_issues) + 1)),
                        title=str(item.get("title", f"Sub-issue {len(sub_issues) + 1}")),
                        description=str(item.get("description", "")),
                        target_files=list(item.get("target_files", []) or []),
                        status="pending",
                    )
                )
            except Exception:
                continue
        if sub_issues:
            return sub_issues[:3]
    return []


def decompose_issue(
    issue_text: str,
    repo_context: str,
    investigation_report: str = "",
) -> List[SubIssue]:
    """Break down an issue into sequential sub-issues if needed."""
    # SWE-bench instances are usually single bugs; skip the LLM call in bench
    # unless explicitly enabled (P1-02: ISHA_BENCH_DECOMPOSE=1 allows up to 3).
    if not LLM_ENABLED or (os.getenv("ISHA_BENCH_MODE", "0") == "1"
                           and os.getenv("ISHA_BENCH_DECOMPOSE", "0") != "1"):
        # Offline / benchmark fallback: single atomic sub-issue
        return [
            SubIssue(
                id=1,
                title="Resolve primary issue",
                description=issue_text.strip(),
                target_files=[],
                status="pending",
            )
        ]

    prompt = f"""You are a senior software architect. Analyze this bug report, investigation report,
and repository context. Determine if this bug should be broken into 1 to 3 ordered, atomic sub-issues,
or if it is already a single atomic fix.

Return a JSON array of sub-issues with the following schema:
[
  {{
    "id": 1,
    "title": "Short title",
    "description": "Specific focus of this step",
    "target_files": ["file1.py"]
  }}
]

Output ONLY the raw JSON array.

BUG REPORT:
{issue_text}

INVESTIGATION REPORT:
{investigation_report[:2000] if investigation_report else "(none)"}

REPO CONTEXT:
{repo_context[:2000] if repo_context else "(none)"}
"""
    try:
        raw_response = call_planner(prompt)
        items = _parse_sub_issues_json(raw_response)
        if items:
            return items
    except Exception:
        pass

    # Default fallback
    return [
        SubIssue(
            id=1,
            title="Core fix",
            description=issue_text.strip(),
            target_files=[],
            status="pending",
        )
    ]


def decomposer_node(state: AgentState) -> AgentState:
    """LangGraph node: analyze complexity and decompose issue into sub-issues."""
    state = coerce_state(state)
    # If already decomposed, skip
    if state.sub_issues:
        return state

    sub_issues = decompose_issue(
        issue_text=state.issue_text,
        repo_context=state.repo_context,
        investigation_report=state.investigation_report,
    )
    state.sub_issues = [s.model_dump() for s in sub_issues]
    state.current_sub_issue_index = 0

    if state.sub_issues:
        curr = state.sub_issues[0]
        curr["status"] = "in_progress"
        # Augment issue text with sub-issue focus if multiple
        if len(state.sub_issues) > 1:
            state.issue_text = (
                f"[Sub-issue 1/{len(state.sub_issues)}: {curr['title']}]\n"
                f"{curr['description']}\n\n"
                f"Overall context: {state.issue_text}"
            )
    return state
