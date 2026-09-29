#!/usr/bin/env python3
"""
ISHA Dashboard — Autonomous Software Engineering Control Room.

    streamlit run src/dashboard/app.py

Tabs:
  1. 🚀 Run & Overview
  2. 📄 Code Diff & Tests
  3. 💻 Download & CLI Export (Apply patch or run in CLI)
  4. 🛡️ Guardrails & Audit
"""

import contextlib
import io
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import streamlit as st

from src.agents.state import AgentState
from src.config import TARGET_REPO_PATH

st.set_page_config(
    page_title="ISHA — Autonomous SWE Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Clean, Premium Styling (Tailored CSS) ─────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    code, pre, .stCode {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Background gradient */
    .stApp {
        background-color: #090d16;
        background-image: 
            radial-gradient(at 10% 10%, rgba(124, 58, 237, 0.12) 0px, transparent 50%),
            radial-gradient(at 90% 90%, rgba(16, 185, 129, 0.08) 0px, transparent 50%);
    }

    /* Top navbar / header card */
    .top-navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.1rem 1.6rem;
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 14px;
        backdrop-filter: blur(16px);
        margin-bottom: 1.5rem;
    }

    .brand-logo {
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        background: linear-gradient(135deg, #ffffff 40%, #c4b5fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .brand-tagline {
        font-size: 0.8rem;
        color: #94a3b8;
        font-weight: 500;
        margin-top: 0.15rem;
    }

    .pill-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.3rem 0.75rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 9999px;
        letter-spacing: 0.02em;
    }

    .badge-success {
        background: rgba(16, 185, 129, 0.14);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.28);
    }

    .badge-purple {
        background: rgba(139, 92, 246, 0.14);
        color: #c4b5fd;
        border: 1px solid rgba(139, 92, 246, 0.28);
    }

    /* Status card */
    .hero-stat-card {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        backdrop-filter: blur(10px);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .hero-stat-card:hover {
        border-color: rgba(139, 92, 246, 0.35);
        transform: translateY(-2px);
    }

    .stat-label {
        font-size: 0.75rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.3rem;
    }

    .stat-value {
        font-size: 1.35rem;
        font-weight: 700;
        color: #f8fafc;
    }

    /* Terminal-like box */
    .cli-box {
        background: #030712;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 0.85rem 1.1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.88rem;
        color: #a7f3d0;
        margin-bottom: 0.8rem;
        overflow-x: auto;
    }

    /* Custom action button styling */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
        border: none;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.95rem;
        padding: 0.6rem 1.2rem;
        box-shadow: 0 4px 16px rgba(124, 58, 237, 0.35);
        transition: all 0.2s ease;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 22px rgba(124, 58, 237, 0.55);
        transform: translateY(-1px);
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.6rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 0.4rem;
        margin-bottom: 1.2rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.45rem 1rem;
        font-weight: 500;
        font-size: 0.9rem;
        color: #94a3b8;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(139, 92, 246, 0.16) !important;
        color: #ddd6fe !important;
        font-weight: 600;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

PRESETS = {
    "Calculator: subtract() bug": "The subtract method in calculator.py returns a+b instead of a-b",
    "Calculator: divide by zero": (
        "divide() in calculator.py doesn't handle division by zero — "
        "divide(10, 0) must raise ValueError('Cannot divide by zero') "
        "instead of ZeroDivisionError"
    ),
    "Multi-file: percentage total": (
        "percentage() in calculator.py is missing the total parameter, "
        "breaking percentage_report in report.py for non-100 totals"
    ),
}

for key, default in (
    ("result", None),
    ("log", ""),
    ("elapsed", 0.0),
    ("thread_id", "ish-0001"),
    ("pending_interrupt", None),
    ("config", None),
    ("applied_to_repo", False),
):
    st.session_state.setdefault(key, default)


def _run(issue_text: str, repo_dir: str) -> None:
    from src.agents.context import build_repo_context
    from src.agents.graph import compiled_multi_graph

    if not repo_dir or not Path(repo_dir).is_dir():
        st.error(f"Repository path not found: `{repo_dir}`")
        return

    st.session_state.applied_to_repo = False
    graph = compiled_multi_graph
    state = AgentState(
        issue_text=issue_text,
        repo_path=repo_dir,
        repo_context=build_repo_context(issue_text, repo_dir),
    )
    st.session_state.thread_id = f"ish-{int(time.time())}"
    st.session_state.config = {
        "configurable": {
            "thread_id": st.session_state.thread_id,
            "approval_mode": "interrupt",
        }
    }

    buffer = io.StringIO()
    started = time.time()
    with contextlib.redirect_stdout(buffer):
        res = graph.invoke(state, st.session_state.config)
    st.session_state.elapsed = time.time() - started
    st.session_state.log = buffer.getvalue()

    interrupts = res.pop("__interrupt__", []) if isinstance(res, dict) else []
    st.session_state.result = res
    st.session_state.pending_interrupt = interrupts[0] if interrupts else None


def _resume(approve: bool) -> None:
    from langgraph.types import Command
    from src.agents.graph import compiled_multi_graph

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        res = compiled_multi_graph.invoke(Command(resume=approve), st.session_state.config)
    st.session_state.log += buffer.getvalue()
    interrupts = res.pop("__interrupt__", []) if isinstance(res, dict) else []
    st.session_state.result = res
    st.session_state.pending_interrupt = interrupts[0] if interrupts else None


# ── Top Navbar ────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="top-navbar">
        <div>
            <h1 class="brand-logo">ISHA · SWE Studio</h1>
            <div class="brand-tagline">Autonomous AI Software Engineer · Red-to-Green TDD Pipeline</div>
        </div>
        <div style="display: flex; gap: 0.6rem; align-items: center;">
            <span class="pill-badge badge-success">🟢 SANDBOX READY</span>
            <span class="pill-badge badge-purple">⚡ GROQ LPU OPTIMIZED</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar Controls ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎯 Issue Setup")
    
    preset = st.selectbox("Quick Preset Issues", ["Custom Issue"] + list(PRESETS.keys()), index=1)
    if preset != "Custom Issue":
        default_val = PRESETS[preset]
    else:
        default_val = "describe the bug or error message here"

    issue_input = st.text_area("Issue Description", default_val, height=130)
    repo_input = st.text_input("Repository Directory", TARGET_REPO_PATH)
    
    st.markdown("---")
    st.markdown("### 🧬 Multi-Agent Fan-Out")
    st.markdown(
        """<div style="font-size: 0.8rem; color: #94a3b8; line-height: 1.5; background: rgba(255,255,255,0.03); padding: 0.7rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 0.8rem;">
        🌿 <b>Worktree A</b>: Minimal Diff<br>
        🌿 <b>Worktree B</b>: Call-Site Aware<br>
        🌿 <b>Worktree C</b>: Alternative Phrasing<br>
        <i>All 3 strategies run in parallel isolated Git worktrees.</i>
        </div>""",
        unsafe_allow_html=True,
    )

    run_btn = st.button("▶️ Run Autonomous Fix", type="primary", use_container_width=True)
    if st.button("🧹 Reset View", use_container_width=True):
        st.session_state.result = None
        st.session_state.log = ""
        st.session_state.pending_interrupt = None
        st.session_state.applied_to_repo = False
        st.rerun()

    st.markdown("---")
    st.caption("🔒 **Safe by Design**: Fixes are explored in isolated sandbox copies. Your real branch is untouched until applied.")

if run_btn:
    with st.spinner("ISHA Multi-Agent is exploring 3 parallel strategies in isolated worktrees…"):
        _run(issue_input, repo_input)

# ── Tab Navigation ────────────────────────────────────────────────────────
tab_run, tab_diff, tab_cli, tab_audit, tab_bench = st.tabs(
    ["🚀 Run & Overview", "📄 Code Diff & Tests", "💻 Download & CLI Export",
     "🛡️ Guardrails & Audit", "📊 Benchmark Runs"]
)

result = st.session_state.result

# ── Tab 1: Run & Overview ──────────────────────────────────────────────────
with tab_run:
    if st.session_state.pending_interrupt is not None:
        payload = st.session_state.pending_interrupt.value
        st.warning("⚠️ **Human Approval Required** — Please review the candidate patch before application.")
        st.json(payload if isinstance(payload, dict) else {"value": str(payload)})
        c_a, c_b = st.columns(2)
        if c_a.button("✅ Approve Fix", type="primary", use_container_width=True):
            _resume(True)
            st.rerun()
        if c_b.button("❌ Reject Fix", use_container_width=True):
            _resume(False)
            st.rerun()

    if not result:
        st.info("👈 Choose an issue on the left sidebar and click **Run Autonomous Fix** to begin.")
    else:
        test_out = result.get("test_output") or ""
        passed = "PASSED" in test_out and "FAILED" not in test_out
        status_color = "#34d399" if passed else "#f87171"
        status_label = "VERIFIED IN SANDBOX" if passed else "ATTENTION NEEDED"

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(
                f"""<div class="hero-stat-card">
                    <div class="stat-label">Resolution Status</div>
                    <div class="stat-value" style="color: {status_color};">{status_label}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""<div class="hero-stat-card">
                    <div class="stat-label">Elapsed Time</div>
                    <div class="stat-value">{st.session_state.elapsed:.2f}s</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f"""<div class="hero-stat-card">
                    <div class="stat-label">Self-Corrections</div>
                    <div class="stat-value">{result.get('retry_count', 0)}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with col4:
            st.markdown(
                f"""<div class="hero-stat-card">
                    <div class="stat-label">Active Strategy</div>
                    <div class="stat-value">{result.get('strategy') or 'TDD Direct'}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📋 Agent Live Transcript & Log", expanded=True):
            st.code(st.session_state.log or "(no console output recorded)", language="text")


# ── Tab 2: Code Diff & Tests ───────────────────────────────────────────────
with tab_diff:
    if not result:
        st.info("Run the agent to inspect the generated code diff and reproduction tests.")
    else:
        st.markdown("#### 🎯 Diagnostic Plan")
        st.info(result.get("plan", "Plan completed."))

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 🧪 TDD Regression Test (Reproduced Bug First)")
            reg = result.get("regression_test", "")
            if reg:
                st.code(reg, language="python")
            else:
                st.caption("No regression test generated.")

        with col_b:
            st.markdown("#### 📝 Clean Code Patch (Unified Diff)")
            patch_text = result.get("patch", "")
            if patch_text:
                st.code(patch_text, language="diff")
            else:
                st.caption("No patch generated.")

        st.markdown("#### 🔬 Sandbox Test Run Output")
        test_out = result.get("test_output", "")
        if test_out:
            st.code(test_out, language="text")
        else:
            st.caption("No test execution output.")


# ── Tab 3: Download & CLI Export (NEW REQUESTED SECTION) ───────────────────
with tab_cli:
    st.markdown("### 💻 Export Fix & CLI Integration")
    st.markdown(
        "Download the validated `.patch` file or execute ISHA directly from your operating system command line."
    )
    st.markdown("<br>", unsafe_allow_html=True)

    patch_str = (result.get("patch") or "") if result else ""

    c_dl, c_apply = st.columns([1.2, 1.8])
    with c_dl:
        st.markdown("#### 📥 1. Download Patch File")
        if patch_str:
            st.download_button(
                label="⬇️ Download isha_fix.patch",
                data=patch_str,
                file_name="isha_fix.patch",
                mime="text/x-diff",
                use_container_width=True,
            )
            st.caption("Standard Git patch ready for `git apply` or code review.")
        else:
            st.button("⬇️ Download isha_fix.patch", disabled=True, use_container_width=True)
            st.caption("Run a fix first to enable download.")

    with c_apply:
        st.markdown("#### 🚀 2. Apply Directly to Local Repository")
        if patch_str and not st.session_state.applied_to_repo:
            if st.button("⚡ Apply Patch to Real Repo Now", type="primary", use_container_width=True):
                from src.tools.patch_engine import apply_patch
                target_p = Path(repo_input).resolve()
                if target_p.is_dir():
                    res = apply_patch(patch_str, str(target_p))
                    if res.applied:
                        st.session_state.applied_to_repo = True
                        st.success(f"✅ Successfully written to `{repo_input}`!")
                    else:
                        st.error(f"Failed to apply: {res.detail}")
                else:
                    st.error("Target repo path does not exist.")
        elif st.session_state.applied_to_repo:
            st.success("✅ Patch is already applied to your repository!")
        else:
            st.button("⚡ Apply Patch to Real Repo Now", disabled=True, use_container_width=True)
            st.caption("Run a fix first to enable direct application.")

    st.markdown("---")
    st.markdown("#### 📟 3. Apply via Git in Your Terminal")
    st.markdown("If you downloaded `isha_fix.patch`, apply it in any terminal with:")
    st.markdown("""<div class="cli-box">git apply isha_fix.patch</div>""", unsafe_allow_html=True)

    st.markdown("#### ⚡ 4. Run ISHA from Command Line Anywhere")
    st.markdown("Run the complete agentic pipeline directly on your project from your PowerShell / bash terminal:")
    cli_issue = issue_input.replace('"', '\\"') if issue_input else "describe your bug"
    st.markdown(
        f"""<div class="cli-box">python src/main.py --repo "{repo_input}" --issue "{cli_issue}" --apply</div>""",
        unsafe_allow_html=True,
    )

    st.markdown("#### 📦 5. Install as a System-Wide CLI Tool")
    st.markdown("Install the `isha` command so you can type `isha \"bug description\"` anywhere:")
    st.markdown(
        """<div class="cli-box"># Inside isha-agent directory:
pip install -e .

# Then use it in any project on your computer:
isha --issue "Cart checkout fails when price is float" --apply</div>""",
        unsafe_allow_html=True,
    )


# ── Tab 4: Guardrails & Audit ─────────────────────────────────────────────
with tab_audit:
    st.markdown("#### 🛡️ Automated Security Guardrail")
    if patch_str:
        from src.guardrails.scanner import scan_patch_for_secrets
        clean, findings = scan_patch_for_secrets(patch_str)
        if clean:
            st.success("✅ **Code Integrity Verified**: No exposed API keys, private credentials, or unsafe file operations detected.")
        else:
            st.error(f"🛑 **Security Warning**: {findings}")
    else:
        st.caption("No patch to inspect yet.")

    st.markdown("---")
    st.markdown("#### 📜 Persistent Approval Audit Trail (`output/approvals.jsonl`)")
    from src.approval.gate import recent_approvals

    records = recent_approvals(limit=50)
    if records:
        st.dataframe(records, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Export Audit Trail (JSONL)",
            "\n".join(json.dumps(r, ensure_ascii=False) for r in records),
            file_name="approvals.jsonl",
            mime="application/jsonl",
            use_container_width=True,
        )
    else:
        st.info("No approval decisions recorded yet.")


# ── Tab 5: Benchmark Runs (Phase 1/8) ──────────────────────────────────────
with tab_bench:
    import glob as _glob

    results_dir = Path(__file__).resolve().parents[2] / "results"
    payload_files = sorted(_glob.glob(str(results_dir / "*.json")))
    runs = []
    for f in payload_files:
        try:
            data = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and data.get("run_id") and "total_instances" in data:
            runs.append((data["run_id"], data))

    plot_img = Path(__file__).resolve().parents[2] / "assets" / "isha_vs_baselines.png"
    if plot_img.exists():
        st.markdown("#### 📈 Empirical Architecture Comparison (Laya-Style Benchmarks)")
        st.image(str(plot_img), caption="ISHA vs Agentless, OpenHands, and Commercial LLM Baselines", use_column_width=True)
        st.markdown("---")

    if not runs:
        st.info(
            "No aggregated benchmark runs yet. Produce one with:\n\n"
            "`python -m src.bench.report <run-id>` or `isha bench --run-id <id> --eval --report`"
        )
    else:
        labels = [rid for rid, _ in runs]
        c_sel, c_cmp = st.columns([2, 2])
        with c_sel:
            pick = st.selectbox("Run", labels, index=len(labels) - 1)
        with c_cmp:
            other = st.selectbox("Compare against", ["(none)"] + labels, index=0)

        payload = dict(runs)[pick]
        n = payload.get("total_instances", 0)
        resolved = payload.get("resolved", 0)
        rate = payload.get("resolve_rate", 0.0)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Instances", n)
        c2.metric("Resolved", resolved)
        c3.metric("Resolve rate", f"{rate:.1%}")
        c4.metric("Mean time", f"{payload.get('mean_elapsed_s', 0):.0f}s")
        c5.metric("Offline answers", payload.get("offline_calls", 0))

        st.markdown("---")
        st.markdown("#### Per-instance results")
        rows = []
        for meta_file in sorted((results_dir / pick).glob("*/meta.json")):
            try:
                m = json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            cands = m.get("candidates") or []
            sel = m.get("selected_candidate") or {}
            log = m.get("model_log") or []
            primary = next(
                (e.get("model") for e in log if e.get("position") == "primary"), "-"
            )
            rows.append({
                "instance": m.get("instance_id"),
                "status": m.get("status"),
                "category": m.get("failure_category") or "-",
                "patch": "yes" if m.get("model_patch") else "no",
                "candidates": len(cands),
                "picked": sel.get("strategy", "-"),
                "score": sel.get("combined_score", "-"),
                "repro": (sel.get("repro") or {}).get("reason", "-"),
                "elapsed_s": round(m.get("elapsed_s", 0) or 0, 1),
                "retries": m.get("retry_count", 0),
                "offline": m.get("offline_calls", 0),
                "primary_model": primary,
            })
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.caption("No per-instance checkpoints found for this run.")

        st.markdown("#### Failure breakdown")
        breakdown = payload.get("breakdown") or {}
        if breakdown:
            # An incomplete run looks like a real result unless it is called
            # out: `not_run` instances were never attempted, so their share of
            # the failure buckets says nothing about the agent.
            not_run = int(breakdown.get("not_run") or 0)
            if not_run:
                st.warning(
                    f"Run incomplete — {not_run} instance(s) were never attempted "
                    f"(`not_run`) and are counted in the denominator. Every other "
                    f"bucket below describes only the instances that actually ran.",
                    icon="⚠️",
                )
            st.json(breakdown)
        else:
            st.caption(
                "No breakdown in this report yet. Regenerate it with "
                "`python -m src.bench.report <run-id>`."
            )

        if other != "(none)":
            from src.bench.report import compare as _compare

            st.markdown("#### Before / After")
            st.markdown(_compare(dict(runs)[other], payload))

        st.markdown("#### LAYA calibration")
        try:
            from src.review import calibration

            model = calibration.load()
            labels_n = calibration.load_labels()
            if model:
                st.json({
                    "mode": model.get("mode"),
                    "n_labels": model.get("n_labels"),
                    "ece_raw": model.get("ece_raw"),
                    "ece_scaled": model.get("ece_scaled"),
                    "brier_raw": model.get("brier_raw"),
                    "brier_scaled": model.get("brier_scaled"),
                    "threshold": model.get("threshold"),
                    "balanced_accuracy": model.get("balanced_accuracy"),
                })
            else:
                st.caption(
                    f"Uncalibrated hand-weighted fallback in use "
                    f"({len(labels_n)} labels collected). Fit with "
                    "`isha bench --fit-laya`."
                )
        except Exception as exc:
            st.caption(f"calibration unavailable: {exc}")
