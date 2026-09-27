#!/usr/bin/env python3
"""
ISHA Dashboard — Streamlit control room.

    streamlit run src/dashboard/app.py

Tabs: Run | Diff | Telemetry | Approvals
"""

import contextlib
import io
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import streamlit as st

from src.agents.state import AgentState

st.set_page_config(page_title="ISHA", page_icon="🤖", layout="wide")

DEFAULT_ISSUE = "subtract method in calculator.py returns a+b instead of a-b"
DEFAULT_REPO = "tests/dummy_repo"

for key, default in (
    ("result", None),
    ("log", ""),
    ("elapsed", 0.0),
    ("thread_id", "ish-0001"),
    ("graph_mode", "Multi-agent (fan-out)"),
    ("pending_interrupt", None),
    ("config", None),
):
    st.session_state.setdefault(key, default)


def _run(issue: str, repo: str, multi: bool) -> None:
    from src.agents.context import build_repo_context
    from src.agents.graph import compiled_graph, compiled_multi_graph

    if not repo or not Path(repo).is_dir():
        st.error(f"Repository path not found: `{repo}` — enter a path to an existing repo.")
        return

    graph = compiled_multi_graph if multi else compiled_graph
    state = AgentState(issue_text=issue, repo_path=repo, repo_context=build_repo_context(issue, repo))
    st.session_state.thread_id = f"ish-{int(time.time())}"
    st.session_state.config = {"configurable": {"thread_id": st.session_state.thread_id, "approval_mode": "interrupt"}}

    buffer = io.StringIO()
    started = time.time()
    with contextlib.redirect_stdout(buffer):
        result = graph.invoke(state, st.session_state.config)
    st.session_state.elapsed = time.time() - started
    st.session_state.log = buffer.getvalue()

    interrupts = result.pop("__interrupt__", []) if isinstance(result, dict) else []
    st.session_state.result = result
    st.session_state.pending_interrupt = interrupts[0] if interrupts else None


def _resume(approve: bool) -> None:
    from langgraph.types import Command

    from src.agents.graph import compiled_multi_graph

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        result = compiled_multi_graph.invoke(Command(resume=approve), st.session_state.config)
    st.session_state.log += buffer.getvalue()
    interrupts = result.pop("__interrupt__", []) if isinstance(result, dict) else []
    st.session_state.result = result
    st.session_state.pending_interrupt = interrupts[0] if interrupts else None


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 ISHA")
    st.caption("Autonomous AI-SWE agent, LAYA-judged")
    issue = st.text_area("Issue / bug report", DEFAULT_ISSUE, height=140)
    repo = st.text_input("Repository path", DEFAULT_REPO)
    mode = st.selectbox("Pipeline", ["Multi-agent (fan-out)", "Single-agent"], index=0)
    run_clicked = st.button("▶️ Run", type="primary", width="stretch")
    if st.button("🧹 Reset", width="stretch"):
        st.session_state.result = None
        st.session_state.log = ""
        st.session_state.pending_interrupt = None
        st.rerun()

if run_clicked:
    with st.spinner("ISHA is working…"):
        _run(issue, repo, mode.startswith("Multi"))

tab_run, tab_diff, tab_telemetry, tab_approvals = st.tabs(
    ["🚀 Run", "📄 Diff", "📊 Telemetry", "✅ Approvals"]
)

# ── Tab 1: Run ─────────────────────────────────────────────────────────────
with tab_run:
    if st.session_state.pending_interrupt is not None:
        payload = st.session_state.pending_interrupt.value
        st.warning("⚠️ Human approval required — LAYA flagged this patch.")
        st.json(payload if isinstance(payload, dict) else {"value": str(payload)})
        col_a, col_b = st.columns(2)
        if col_a.button("✅ Approve", type="primary"):
            _resume(True)
            st.rerun()
        if col_b.button("❌ Reject"):
            _resume(False)
            st.rerun()

    result = st.session_state.result
    if not result:
        st.info("Set an issue on the left and press **Run**.")
    else:
        st.success(f"Finished in {st.session_state.elapsed:.1f}s")
        st.markdown(f"**Verdict:** `{result.get('critic_verdict')}` · "
                    f"**score:** {result.get('critic_score', 0):.3f} · "
                    f"**strategy:** `{result.get('strategy')}` · "
                    f"**retries:** {result.get('retry_count')}")
        approved = result.get("approved")
        st.markdown(f"**Approval:** {'✅ approved' if approved else ('⚠️ awaiting human' if approved is None else '❌ rejected')}")
        with st.expander("Agent transcript", expanded=True):
            st.code(st.session_state.log or "(no output)", language="text")

# ── Tab 2: Diff ────────────────────────────────────────────────────────────
with tab_diff:
    result = st.session_state.result
    if not result:
        st.info("Run the agent to see the patch.")
    else:
        st.subheader("Plan")
        st.text(result.get("plan", ""))
        st.subheader("Regression test")
        st.code(result.get("regression_test", ""), language="python")
        st.subheader("Patch")
        patch = result.get("patch", "")
        if patch:
            st.code(patch, language="diff")
            from src.guardrails.scanner import scan_patch_for_secrets

            clean, findings = scan_patch_for_secrets(patch)
            if clean:
                st.success("Guardrail scan: clean ✅")
            else:
                st.error(f"Guardrail findings: {findings}")
        else:
            st.warning("No patch produced.")
        with st.expander("Test output"):
            st.code(result.get("test_output", ""), language="text")

# ── Tab 3: Telemetry ──────────────────────────────────────────────────────
with tab_telemetry:
    result = st.session_state.result
    if not result:
        st.info("Run the agent to see telemetry.")
    else:
        scores = result.get("laya_scores", {}) or {}
        st.subheader("LAYA scores")
        for key in ("fix_quality", "matches_issue", "safe_to_apply", "composite", "secrets_or_danger", "logic_drift"):
            if key in scores and isinstance(scores[key], (int, float)):
                value = float(scores[key])
                scale = 2.0 if key == "fix_quality" else 1.0
                st.progress(min(1.0, value / scale), text=f"{key}: {value:.3f} / {scale:.1f}")
        if scores.get("guardrail_findings"):
            st.error(f"Guardrail findings: {scores['guardrail_findings']}")

        st.subheader("Attempt ledger")
        from src.review.arbitration import peek_attempts

        attempts = peek_attempts(st.session_state.thread_id)
        if attempts:
            st.dataframe(attempts, width="stretch", hide_index=True)
        else:
            st.caption("No recorded attempts for this thread.")

        st.subheader("Run metrics")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Elapsed", f"{st.session_state.elapsed:.1f}s")
        m2.metric("Retries", result.get("retry_count", 0))
        m3.metric("Composite", f"{result.get('critic_score', 0):.3f}")
        m4.metric("Candidates", scores.get("candidates", "—"))

# ── Tab 4: Approvals ──────────────────────────────────────────────────────
with tab_approvals:
    from src.approval.gate import recent_approvals

    st.subheader("Audit trail (approvals.jsonl)")
    rows = recent_approvals(limit=50)
    if rows:
        st.dataframe(rows, width="stretch", hide_index=True)
        st.download_button("⬇️ Export JSONL", "\n".join(
            __import__("json").dumps(r, ensure_ascii=False) for r in rows
        ), file_name="approvals.jsonl", mime="application/jsonl")
    else:
        st.info("No approval decisions recorded yet.")
    st.caption("Auto-approved runs are logged too — flagged diffs pause for a human in the Run tab.")
