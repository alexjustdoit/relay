"""
Relay — Handoff History
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

st.markdown("<style>[data-testid='stSidebarNav'],[data-testid='stSidebarNavItems'],[data-testid='stSidebarNavLink']{display:none!important}</style>", unsafe_allow_html=True)
st.markdown("""
<style>
.main .block-container,
.stMainBlockContainer,
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"] {
    padding-top: 1.5rem !important;
}
</style>
""", unsafe_allow_html=True)

import config  # noqa: F401
from data.store import load_history, delete_history_entry, clear_history
from gdrive.auth import get_credentials
from gdrive.drive import create_handoff_doc

st.markdown("## History")
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
    try:
        ts = datetime.fromisoformat(entry["timestamp"])
        ts_display = ts.strftime("%-m/%-d/%Y · %-I:%M %p")
    except Exception:
        ts_display = entry["timestamp"]
    header = f"**{entry['account_name']}** — {type_label} · {ts_display}"
    with st.expander(header):
        st.markdown(entry["output"])
        st.divider()
        doc_title = f"{entry['account_name']} — {type_label} Handoff"
        safe_title = doc_title
        for ch in ("→", "—", "/", "\\", ":", "|", "?", "*", "<", ">", '"'):
            safe_title = safe_title.replace(ch, "-")
        creds = get_credentials()
        gdrive_connected = creds is not None and not creds.expired

        col_gdrive, col_txt, col_pdf, col_del = st.columns([1, 1, 1, 1])
        with col_gdrive:
            if gdrive_connected:
                if st.button("Save to Drive", key=f"gdrive_{entry['id']}", use_container_width=True, type="primary"):
                    with st.spinner("Saving..."):
                        try:
                            url = create_handoff_doc(creds, doc_title, entry["output"])
                            st.success(f"[Open in Google Docs]({url})")
                        except Exception as e:
                            st.error(f"Failed: {e}")
            else:
                st.caption("Sign in to save to Drive")
        with col_txt:
            st.download_button(
                label="Download .txt",
                data=entry["output"],
                file_name=f"{safe_title}.txt",
                mime="text/plain",
                key=f"dl_{entry['id']}",
                use_container_width=True,
            )
        with col_pdf:
            try:
                from app.pdf_export import generate_pdf
                pdf_bytes = generate_pdf(entry["output"])
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name=f"{safe_title}.pdf",
                    mime="application/pdf",
                    key=f"pdf_{entry['id']}",
                    use_container_width=True,
                )
            except Exception:
                st.caption("PDF unavailable")
        with col_del:
            if st.button("Delete", key=f"del_{entry['id']}", use_container_width=True):
                delete_history_entry(entry["id"])
                st.rerun()
