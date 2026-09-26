"""
ISHA Approval Gate — human sign-off before anything is committed.

Two modes:
  * cli        — prints the diff, waits for y/n on the terminal
  * interrupt  — LangGraph interrupt() so the Streamlit dashboard can resume
  * auto       — record the decision and leave `approved = None` for review

Every decision is appended to approvals.jsonl as an audit trail.
"""

import datetime
import json
import os
import threading

from langgraph.types import RunnableConfig

from src.agents.state import AgentState, coerce_state
from src.guardrails.scanner import scan

APPROVALS_FILE = os.getenv("ISHA_APPROVALS_FILE", "approvals.jsonl")
_LOCK = threading.Lock()


def log_approval(entry: dict) -> dict:
    """Append one audit record to approvals.jsonl."""
    record = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), **entry}
    try:
        with _LOCK:
            with open(APPROVALS_FILE, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        record["log_error"] = str(exc)
    return record


def recent_approvals(limit: int = 5) -> list:
    """Return the newest audit records (for the telemetry tab)."""
    if not os.path.exists(APPROVALS_FILE):
        return []
    try:
        with open(APPROVALS_FILE, "r", encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
        return rows[-limit:][::-1]
    except (OSError, json.JSONDecodeError):
        return []


def approval_node(state, config: RunnableConfig | None = None) -> AgentState:
    """Pause for human approval when the diff was flagged or blocked."""
    state = coerce_state(state)
    options = (config or {}).get("configurable", {}) if isinstance(config, dict) else {}
    if not options and config is not None:
        options = dict(config.get("configurable", {}))

    report = scan(state.patch, state.issue_text)
    needs_review = state.critic_verdict == "flagged" or report["blocked"]

    entry = {
        "issue": state.issue_text,
        "verdict": state.critic_verdict,
        "score": state.critic_score,
        "strategy": state.strategy,
        "laya_scores": state.laya_scores,
        "guardrails": report,
        "patch_preview": (state.patch or "")[:1200],
    }

    if not needs_review:
        state.approved = True
        log_approval({**entry, "decision": "auto_approved"})
        return state

    mode = options.get("approval_mode", "auto")

    if mode == "interrupt":
        from langgraph.interrupt import interrupt

        decision = interrupt(
            {
                "type": "approval_required",
                "issue": state.issue_text,
                "patch": state.patch,
                "verdict": state.critic_verdict,
                "score": state.critic_score,
                "guardrails": report,
            }
        )
        state.approved = bool(decision and str(decision).lower() in {"approve", "approved", "y", "yes", "true"})
    elif mode == "cli":
        print("\n" + "=" * 60)
        print("  ⚠️  HUMAN APPROVAL REQUIRED")
        print("=" * 60)
        print(f"  Issue:  {state.issue_text}")
        print(f"  Verdict:{state.critic_verdict}  score={state.critic_score:.3f}")
        if report["patch_findings"]:
            print(f"  Guardrail findings: {report['patch_findings']}")
        print("-" * 60)
        print(state.patch or "(no patch)")
        print("-" * 60)
        try:
            answer = input("  Approve this patch? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"
        state.approved = answer in {"y", "yes"}
    else:
        state.approved = None

    log_approval({**entry, "decision": "approved" if state.approved else "rejected"})
    return state
