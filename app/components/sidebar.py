"""
Sidebar for Relay — branding + Google Drive connection status.
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

_BRANDING_HTML = """
<div style="min-height: 110px;">
  <div style="display:flex; justify-content:center; padding: 0.75rem 0 0.5rem 0;">
    <svg width="48" height="44" viewBox="0 0 48 44" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="2" y="18" width="20" height="8" rx="4" fill="#E8923A" opacity="0.55"/>
      <rect x="26" y="18" width="20" height="8" rx="4" fill="#E8923A"/>
      <circle cx="24" cy="22" r="6" fill="#E8923A"/>
      <circle cx="24" cy="22" r="3" fill="white"/>
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


def render_sidebar_footer():
    from gdrive.auth import get_credentials, get_auth_url, revoke

    with st.sidebar:
        st.markdown('<div class="sidebar-footer-spacer"></div>', unsafe_allow_html=True)
        st.divider()

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
