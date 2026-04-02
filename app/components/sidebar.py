"""
Sidebar for Relay — branding + Google Drive connection status.
"""
import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from gdrive.auth import get_credentials, get_auth_url, revoke

_BRANDING_HTML = """
<div style="min-height: 130px;">
  <div style="display:flex; justify-content:center; padding: 0.75rem 0 0.5rem 0;">
    <svg width="44" height="44" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M4 22 L18 22" stroke="#E8923A" stroke-width="2.5" stroke-linecap="round" opacity="0.45"/>
      <path d="M12 15 L20 22 L12 29" stroke="#E8923A" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.45"/>
      <path d="M24 22 L40 22" stroke="#E8923A" stroke-width="2.5" stroke-linecap="round"/>
      <path d="M32 15 L40 22 L32 29" stroke="#E8923A" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="22" cy="22" r="3.5" fill="#E8923A"/>
    </svg>
  </div>
  <p style="font-size: 1.75rem; font-weight: 700; line-height: 1.2; margin: 0 0 0.2rem 0;">Relay</p>
  <p style="font-size: 0.875rem; opacity: 0.6; margin: 0; line-height: 1.4;">Account Handoff Builder</p>
</div>
"""

_SIDEBAR_CSS = """<style>
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavLink"] { display: none !important; }
section[data-testid="stSidebar"] [data-testid="stLogoSpacer"] {
    display: none !important; height: 0 !important; min-height: 0 !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    min-height: 0 !important; height: auto !important; padding: 0 !important;
}
[data-testid="stSidebarContent"] {
    display: flex !important; flex-direction: column !important; min-height: 100vh !important;
}
[data-testid="stSidebarUserContent"] {
    flex: 1 !important; display: flex !important; flex-direction: column !important;
    min-height: 0 !important; padding-top: 0.5rem !important;
}
[data-testid="stSidebarUserContent"] > div:first-child {
    flex: 1 !important; display: flex !important; flex-direction: column !important; min-height: 0 !important;
}
[data-testid="stSidebarUserContent"] > div:first-child > [data-testid="stVerticalBlock"] {
    flex: 1 !important; display: flex !important; flex-direction: column !important; min-height: 0 !important;
}
.element-container:has(.sidebar-footer-spacer) { flex: 1 !important; min-height: 0 !important; }
</style>"""


def render_sidebar_header():
    with st.sidebar:
        st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)
        st.markdown(_BRANDING_HTML, unsafe_allow_html=True)
        st.divider()


def render_sidebar_footer(dev_pages=None):
    with st.sidebar:
        st.markdown('<div class="sidebar-footer-spacer"></div>', unsafe_allow_html=True)
        st.divider()

        # LLM Provider toggle
        st.subheader("LLM Provider")
        if config.SCC_MODE:
            st.toggle(
                "Use Local LLM (Ollama)",
                value=False,
                disabled=True,
                help="Local Ollama is not available on the hosted demo — the app uses OpenAI automatically.",
            )
            st.caption("Demo uses OpenAI API · Local Ollama available when self-hosted")
        else:
            use_local = st.toggle(
                "Use Local LLM (Ollama)",
                value=os.getenv("USE_LOCAL_LLM", "false").lower() == "true",
                help="Toggle between free local Ollama and OpenAI API",
            )
            os.environ["USE_LOCAL_LLM"] = "true" if use_local else "false"

            if use_local:
                model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
                st.caption(f"Local mode · Free · {model}")
            else:
                if os.getenv("OPENAI_API_KEY"):
                    st.caption("✅ OpenAI key set")
                else:
                    st.warning("Set OPENAI_API_KEY in .env")

        st.divider()

        # Google Drive connection
        creds = get_credentials()
        connected = creds is not None and not creds.expired

        if connected:
            st.caption("✅ Google Drive connected")
            if st.button("Disconnect Drive", use_container_width=True):
                revoke()
                st.rerun()
        else:
            st.markdown("**Google Drive**")
            st.caption("Connect to save handoffs as Google Docs")
            auth_url = get_auth_url()
            st.link_button("Connect Google Drive", auth_url, use_container_width=True)

        # Developers section
        if dev_pages:
            st.divider()
            with st.expander("Developers"):
                for page in dev_pages:
                    st.page_link(page)
