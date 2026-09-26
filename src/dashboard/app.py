"""
ISHA Dashboard — Streamlit live-state viewer.

Full implementation with 4 tabs in Phase 9. For now, a minimal landing page.
"""

import streamlit as st

st.set_page_config(
    page_title="ISHA — AI-SWE Agent",
    page_icon="🤖",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 2rem 0;
    }
    .sub-header {
        text-align: center;
        color: #888;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .status-card {
        background: #1a1a2e;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #333;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-header">🤖 ISHA</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Autonomous AI Software Engineering Agent</div>',
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Status", "Ready ✅")

with col2:
    st.metric("LAYA Engine", "Loaded")

with col3:
    st.metric("Phase", "1 — Skeleton")

st.divider()
st.info("🚧 Full dashboard with 4 tabs coming in Phase 9. Run `streamlit run src/dashboard/app.py` to see this page.")
