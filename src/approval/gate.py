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

# P0-13: anchor to repo ROOT (was CWD-relative, broke when invoked elsewhere).
_ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
_DEFAULT_APPROVALS = str(_ROOT / "output" / "approvals.jsonl")
APPROVALS_FILE = os.getenv("ISHA_APPROVALS_FILE", _DEFAULT_APPROVALS)
_LOCK = threading.Lock()


def _approvals_file() -> str:
    return os.getenv("ISHA_APPROVALS_FILE", _DEFAULT_APPROVALS)


def log_approval(entry: dict) -> dict:
    """Append one audit record to approvals.jsonl."""
    record = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), **entry}
    try:
        with _LOCK:
            with open(_approvals_file(), "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        record["log_error"] = str(exc)
    return record


def recent_approvals(limit: int = 5) -> list:
    """Return the newest audit records (for the telemetry tab)."""
    path = _approvals_file()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
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

    # AR-4 #6: optional per-org calibrated auto-approve gate. Default OFF so
    # benchmark lanes and Docker evals keep their exact historical behavior;
    # enable with ISHA_PER_ORG_GATE=1 on interactive/CI runs.
    per_org_gate = os.getenv("ISHA_PER_ORG_GATE", "0").strip().lower()
    if not needs_review and per_org_gate not in {"0", "", "false", "off"}:
        from src.memory.store import org_of
        from src.review.calibration import per_org_threshold

        try:
            prob = float((state.laya_scores or {}).get("combined"))  # None-safe
        except (TypeError, ValueError):
            prob = None
        org = org_of(getattr(state, "instance_id", "") or "", state.repo_path or "")
        thr = per_org_threshold(org)
        if prob is not None and thr is not None and prob < thr:
            needs_review = True
            entry["per_org_gate"] = {"org": org, "prob": prob, "threshold": thr}

    if not needs_review:
        state.approved = True
        log_approval({**entry, "decision": "auto_approved"})
        return state

    mode = options.get("approval_mode", "auto")

    if mode == "interrupt":
        from langgraph.types import interrupt

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

    # P0-13: log None as pending (was logged as rejected).
    decision = "approved" if state.approved is True else ("pending" if state.approved is None else "rejected")
    log_approval({**entry, "decision": decision})
    return state
