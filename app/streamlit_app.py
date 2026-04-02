"""
Relay — Account Handoff Builder
Run with: streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

import config  # noqa: F401 — loads .env
from app.components.sidebar import render_sidebar_header, render_sidebar_footer
from gdrive.auth import exchange_code

st.set_page_config(
    page_title="Relay",
    page_icon="🔁",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("<style>[data-testid='stSidebarNav'],[data-testid='stSidebarNavItems'],[data-testid='stSidebarNavLink']{display:none!important}</style>", unsafe_allow_html=True)

_GLOBAL_CSS = """
<style>
.main .block-container,
.stMainBlockContainer,
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"] {
    padding-top: 1.5rem !important;
}
[data-testid="stButton"] button[kind="primary"] {
    background-color: #E8923A !important;
    border-color: #E8923A !important;
}
[data-testid="stButton"] button[kind="primary"]:hover {
    background-color: #d07d2e !important;
    border-color: #d07d2e !important;
}
.type-card {
    border: 2px solid #333;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    height: 100%;
}
</style>
"""


def _handle_oauth_callback():
    params = st.query_params
    if "code" in params and "google_creds" not in st.session_state:
        with st.spinner("Connecting Google Drive..."):
            try:
                exchange_code(params["code"])
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Google Drive connection failed: {e}")
                st.caption(f"Redirect URI in use: `{config.GOOGLE_REDIRECT_URI}`")
                st.query_params.clear()


def home():
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)
    _handle_oauth_callback()

    st.title("Relay")
    st.markdown("Build a professional account handoff document in minutes — structured input, AI gap detection, and a narrative your recipient can act on immediately.")
    st.divider()

    st.subheader("Start a New Handoff")
    st.markdown("Choose the type of handoff you're creating.")
    st.markdown("")

    col1, col2, col_spacer = st.columns([1, 1, 2])

    with col1:
        st.markdown("""
        <div class="type-card">
            <div style="font-size:2.5rem; margin-bottom:0.75rem;">🤝</div>
            <div style="font-size:1.1rem; font-weight:700; margin-bottom:0.4rem;">Sales → CS</div>
            <div style="font-size:0.85rem; opacity:0.7; line-height:1.4;">Hand off a new customer from Sales to Customer Success</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")
        if st.button("Start Sales → CS", key="home_sales_to_cs", type="primary", use_container_width=True):
            st.session_state["_form_version"] = st.session_state.get("_form_version", 0) + 1
            st.session_state["handoff_type"] = "sales_to_cs"
            st.session_state["form_data"] = {}
            st.session_state.pop("generated_output", None)
            st.session_state.pop("gaps", None)
            st.switch_page("pages/1_Builder.py")

    with col2:
        st.markdown("""
        <div class="type-card">
            <div style="font-size:2.5rem; margin-bottom:0.75rem;">🔁</div>
            <div style="font-size:1.1rem; font-weight:700; margin-bottom:0.4rem;">TAM → TAM</div>
            <div style="font-size:0.85rem; opacity:0.7; line-height:1.4;">Transfer an existing account between Technical Account Managers</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")
        if st.button("Start TAM → TAM", key="home_tam_to_tam", type="primary", use_container_width=True):
            st.session_state["_form_version"] = st.session_state.get("_form_version", 0) + 1
            st.session_state["handoff_type"] = "tam_to_tam"
            st.session_state["form_data"] = {}
            st.session_state.pop("generated_output", None)
            st.session_state.pop("gaps", None)
            st.switch_page("pages/1_Builder.py")

    st.divider()

    st.subheader("How it works")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**1. Fill the form**")
        st.markdown("Structured fields covering everything the recipient needs — stakeholders, commitments, red flags, in-flight work, and more.")
    with c2:
        st.markdown("**2. Check for gaps**")
        st.markdown("Before generating, AI reviews your inputs and flags missing or thin fields inline so you can fix them first.")
    with c3:
        st.markdown("**3. Generate & save**")
        st.markdown("Get a professional narrative document with an AI-contributed onboarding plan. Save to Google Drive or download as text.")


home_page = st.Page(home, title="Home", default=True)
builder_page = st.Page("pages/1_Builder.py", title="New Handoff")
history_page = st.Page("pages/2_History.py", title="History")
tech_info_page = st.Page("pages/3_Technical_Info.py", title="Technical Info")

pg = st.navigation([home_page, builder_page, history_page, tech_info_page], position="hidden")

render_sidebar_header()

with st.sidebar:
    st.page_link(home_page)
    if st.button("New Handoff", key="sidebar_new_handoff", use_container_width=True):
        st.session_state["_new_handoff_clicked"] = True
        st.switch_page("pages/1_Builder.py")
    st.page_link(history_page)

pg.run()
render_sidebar_footer(dev_pages=[tech_info_page])
