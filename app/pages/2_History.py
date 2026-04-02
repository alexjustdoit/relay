"""
Relay — Handoff History
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

st.markdown("<style>[data-testid='stSidebarNav'],[data-testid='stSidebarNavItems'],[data-testid='stSidebarNavLink']{display:none!important}</style>", unsafe_allow_html=True)

import config  # noqa: F401
from data.store import load_history, delete_history_entry, clear_history

st.title("History")
st.caption("Your last 50 generated handoffs. Persists across restarts when running locally; session-only on the hosted demo.")

history = load_history()

if not history:
    st.info("No handoffs saved yet. Generate one from the Builder.")
    st.stop()

col_hdr, col_clear = st.columns([6, 1])
with col_clear:
    if st.button("Clear All", use_container_width=True):
        clear_history()
        st.rerun()

st.divider()

for entry in history:
    type_label = "Sales → CS" if entry["handoff_type"] == "sales_to_cs" else "TAM → TAM"
    header = f"**{entry['account_name']}** — {type_label} · {entry['timestamp']}"
    with st.expander(header):
        st.markdown(entry["output"])
        st.divider()
        if st.button("Delete", key=f"del_{entry['id']}"):
            delete_history_entry(entry["id"])
            st.rerun()
