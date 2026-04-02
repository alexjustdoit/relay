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
from gdrive.auth import exchange_code, get_credentials
from llm.gap_detection import detect_gaps
from llm.generation import stream_handoff
from gdrive.drive import create_handoff_doc

st.set_page_config(
    page_title="Relay",
    page_icon="🔁",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main .block-container,
.stMainBlockContainer,
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"] {
    padding-top: 1.5rem !important;
}
/* Type selection cards */
.type-card {
    border: 2px solid #333;
    border-radius: 12px;
    padding: 1.5rem;
    cursor: pointer;
    transition: border-color 0.2s;
    text-align: center;
}
.type-card:hover { border-color: #E8923A; }
.type-card-selected { border-color: #E8923A !important; background: rgba(232,146,58,0.08); }
/* Accent button color */
[data-testid="stButton"] button[kind="primary"] {
    background-color: #E8923A !important;
    border-color: #E8923A !important;
}
[data-testid="stButton"] button[kind="primary"]:hover {
    background-color: #d07d2e !important;
    border-color: #d07d2e !important;
}
/* Gap detection badges */
.gap-error { color: #e74c3c; font-size: 0.85rem; }
.gap-warning { color: #f0a500; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)


# ── OAuth callback handling ────────────────────────────────────────────────────

def _handle_oauth_callback():
    params = st.query_params
    if "code" in params and "google_creds" not in st.session_state:
        with st.spinner("Connecting Google Drive..."):
            try:
                exchange_code(params["code"])
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Google auth failed: {e}")
                st.query_params.clear()


# ── Type selection ─────────────────────────────────────────────────────────────

_TYPE_LABELS = {
    "sales_to_cs": ("Sales → CS", "Hand off a new customer from Sales to Customer Success"),
    "tam_to_tam": ("TAM → TAM", "Transfer an existing account between Technical Account Managers"),
}


def render_type_selection():
    st.title("New Handoff")
    st.markdown("Choose the type of handoff you're creating.")
    st.markdown("")

    col1, col2, col_spacer = st.columns([1, 1, 2])
    current = st.session_state.get("handoff_type")

    with col1:
        selected_s = current == "sales_to_cs"
        card_class = "type-card type-card-selected" if selected_s else "type-card"
        st.markdown(f"""
        <div class="{card_class}">
            <div style="font-size:2rem;">🤝</div>
            <div style="font-size:1.1rem; font-weight:700; margin:0.5rem 0 0.25rem;">Sales → CS</div>
            <div style="font-size:0.85rem; opacity:0.7;">Hand off a new customer from Sales to Customer Success</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")
        if st.button("Select", key="btn_sales_to_cs", use_container_width=True,
                     type="primary" if selected_s else "secondary"):
            _set_type("sales_to_cs")

    with col2:
        selected_t = current == "tam_to_tam"
        card_class = "type-card type-card-selected" if selected_t else "type-card"
        st.markdown(f"""
        <div class="{card_class}">
            <div style="font-size:2rem;">🔁</div>
            <div style="font-size:1.1rem; font-weight:700; margin:0.5rem 0 0.25rem;">TAM → TAM</div>
            <div style="font-size:0.85rem; opacity:0.7;">Transfer an existing account between Technical Account Managers</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")
        if st.button("Select", key="btn_tam_to_tam", use_container_width=True,
                     type="primary" if selected_t else "secondary"):
            _set_type("tam_to_tam")


def _set_type(t: str):
    existing = st.session_state.get("handoff_type")
    form = st.session_state.get("form_data", {})
    has_data = any(v for v in form.values() if v)

    if existing and existing != t and has_data:
        st.session_state["pending_type_change"] = t
    else:
        st.session_state["handoff_type"] = t
        st.session_state.pop("form_data", None)
        st.session_state.pop("generated_output", None)
        st.session_state.pop("gaps", None)
        st.rerun()


def _handle_type_change_dialog():
    if "pending_type_change" not in st.session_state:
        return
    pending = st.session_state["pending_type_change"]
    label = _TYPE_LABELS[pending][0]
    st.warning(f"Switching to **{label}** will clear your current form. Continue?")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Yes, switch", type="primary", use_container_width=True):
            st.session_state["handoff_type"] = pending
            st.session_state.pop("pending_type_change", None)
            st.session_state.pop("form_data", None)
            st.session_state.pop("generated_output", None)
            st.session_state.pop("gaps", None)
            st.rerun()
    with c2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.pop("pending_type_change", None)
            st.rerun()


# ── Form helpers ───────────────────────────────────────────────────────────────

def _fd(key, default=""):
    """Get a value from form_data in session state."""
    return st.session_state.get("form_data", {}).get(key, default)


def _save_fd(key, value):
    if "form_data" not in st.session_state:
        st.session_state["form_data"] = {}
    st.session_state["form_data"][key] = value


def _gap_hint(gaps: list[dict], field: str):
    """Render an inline gap hint for a field if one exists."""
    for g in gaps:
        if g.get("field", "").lower().replace(" ", "_") == field.lower().replace(" ", "_"):
            icon = "🔴" if g["severity"] == "error" else "🟡"
            css = "gap-error" if g["severity"] == "error" else "gap-warning"
            st.markdown(f'<span class="{css}">{icon} {g["message"]}</span>', unsafe_allow_html=True)
            return


# ── Stakeholder rows ───────────────────────────────────────────────────────────

def render_stakeholder_rows(key_prefix: str, gaps: list):
    st.markdown("**Stakeholders**")
    if "stakeholders" not in st.session_state.get("form_data", {}):
        _save_fd("stakeholders", [{"name": "", "title": "", "role": "", "savviness": "", "sentiment": ""}])

    rows = _fd("stakeholders", [{"name": "", "title": "", "role": "", "savviness": "", "sentiment": ""}])
    updated = []

    for i, row in enumerate(rows):
        with st.expander(f"Stakeholder {i+1}" + (f" — {row['name']}" if row['name'] else ""), expanded=i == 0):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Name", value=row.get("name", ""), key=f"{key_prefix}_sk_name_{i}")
                title = st.text_input("Title", value=row.get("title", ""), key=f"{key_prefix}_sk_title_{i}")
                role = st.text_input("Role (e.g. Champion, Economic Buyer, Technical DRI)",
                                     value=row.get("role", ""), key=f"{key_prefix}_sk_role_{i}")
            with c2:
                savviness = st.text_input("Technical Savviness", value=row.get("savviness", ""),
                                          key=f"{key_prefix}_sk_sav_{i}",
                                          placeholder="e.g. Deep Python/cloud background, not hands-on with infra")
                sentiment = st.selectbox("Sentiment", ["", "Champion", "Positive", "Neutral", "Skeptical", "Detractor"],
                                         index=["", "Champion", "Positive", "Neutral", "Skeptical", "Detractor"].index(row.get("sentiment", "")),
                                         key=f"{key_prefix}_sk_sent_{i}")
            updated.append({"name": name, "title": title, "role": role,
                            "savviness": savviness, "sentiment": sentiment})

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("+ Add Stakeholder", key=f"{key_prefix}_add_sk"):
            updated.append({"name": "", "title": "", "role": "", "savviness": "", "sentiment": ""})
    if len(updated) > 1:
        with col2:
            if st.button("Remove last", key=f"{key_prefix}_rm_sk"):
                updated = updated[:-1]

    _save_fd("stakeholders", updated)


# ── Red flags rows ─────────────────────────────────────────────────────────────

def render_red_flags(key_prefix: str, gaps: list):
    st.markdown("**Red Flags & Risks**")
    if "red_flags" not in st.session_state.get("form_data", {}):
        _save_fd("red_flags", [{"category": "", "description": ""}])

    flags = _fd("red_flags", [{"category": "", "description": ""}])
    updated = []
    categories = ["Technical Risk", "Relationship Risk", "Commercial Risk", "Adoption Risk", "Other"]

    for i, flag in enumerate(flags):
        c1, c2 = st.columns([1, 2])
        with c1:
            cat = st.selectbox("Category", [""] + categories,
                               index=([""] + categories).index(flag.get("category", "")) if flag.get("category", "") in ([""] + categories) else 0,
                               key=f"{key_prefix}_flag_cat_{i}")
        with c2:
            desc = st.text_input("Description", value=flag.get("description", ""),
                                 key=f"{key_prefix}_flag_desc_{i}",
                                 placeholder="Be specific — what happened or could happen?")
        updated.append({"category": cat, "description": desc})

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("+ Add Flag", key=f"{key_prefix}_add_flag"):
            updated.append({"category": "", "description": ""})
    if len(updated) > 1:
        with col2:
            if st.button("Remove last", key=f"{key_prefix}_rm_flag"):
                updated = updated[:-1]

    _save_fd("red_flags", updated)


# ── Sales → CS form ────────────────────────────────────────────────────────────

def render_sales_to_cs_form(gaps: list):
    st.markdown("## Sales → CS Handoff")
    _handle_type_change_link()
    st.divider()

    # Account Overview
    st.subheader("Account Overview")
    c1, c2 = st.columns(2)
    with c1:
        v = st.text_input("Account Name *", value=_fd("account_name"), key="s_account_name")
        _save_fd("account_name", v)
        _gap_hint(gaps, "account_name")

        v = st.text_input("Product / Plan", value=_fd("product"), key="s_product")
        _save_fd("product", v)
    with c2:
        v = st.text_input("ARR", value=_fd("arr"), key="s_arr", placeholder="e.g. $120,000")
        _save_fd("arr", v)

        v = st.text_input("Close Date", value=_fd("close_date"), key="s_close_date", placeholder="e.g. 2026-04-15")
        _save_fd("close_date", v)

    st.divider()

    # Why They Bought
    st.subheader("Why They Bought")
    _gap_hint(gaps, "pain_points")
    v = st.text_area("Pain Points / Use Case", value=_fd("pain_points"), key="s_pain_points", height=100,
                     placeholder="What problem were they trying to solve? Why now?")
    _save_fd("pain_points", v)

    v = st.text_area("Success Criteria", value=_fd("success_criteria"), key="s_success_criteria", height=80,
                     placeholder="How will they measure success in the first 90 days?")
    _save_fd("success_criteria", v)
    _gap_hint(gaps, "success_criteria")

    v = st.text_input("Competitors Evaluated", value=_fd("competitors"), key="s_competitors",
                      placeholder="e.g. Considered Competitor A and B, went with us because of X")
    _save_fd("competitors", v)

    st.divider()

    # Stakeholders
    render_stakeholder_rows("s", gaps)
    st.divider()

    # Commitments
    st.subheader("Commitments & Promises")
    v = st.text_area("Written Commitments (in contract or email)", value=_fd("commitments_written"),
                     key="s_comm_written", height=80,
                     placeholder="e.g. Dedicated onboarding engineer for 60 days")
    _save_fd("commitments_written", v)

    v = st.text_area("Verbal / Unwritten Commitments", value=_fd("commitments_verbal"),
                     key="s_comm_verbal", height=80,
                     placeholder="Anything promised in calls that isn't in writing")
    _save_fd("commitments_verbal", v)

    v = st.text_area("Functionality Promises (things that don't exist yet)", value=_fd("commitments_functionality"),
                     key="s_comm_func", height=80,
                     placeholder="Features or capabilities promised that are on the roadmap or TBD")
    _save_fd("commitments_functionality", v)
    _gap_hint(gaps, "commitments")

    st.divider()

    # Red Flags
    render_red_flags("s", gaps)
    st.divider()

    # Key Dates
    st.subheader("Key Upcoming Dates")
    v = st.text_area("Known Upcoming Dates", value=_fd("key_dates"), key="s_key_dates", height=80,
                     placeholder="e.g. Go-live target: May 1 · Exec review: June · SKO: August")
    _save_fd("key_dates", v)
    st.divider()

    # Misc
    st.subheader("Additional Notes")
    v = st.text_area("Anything else the CSM should know?", value=_fd("misc_notes"), key="s_misc_notes", height=100)
    _save_fd("misc_notes", v)


# ── TAM → TAM form ─────────────────────────────────────────────────────────────

def render_tam_to_tam_form(gaps: list):
    st.markdown("## TAM → TAM Handoff")
    _handle_type_change_link()
    st.divider()

    # Account Overview
    st.subheader("Account Overview")
    c1, c2, c3 = st.columns(3)
    with c1:
        v = st.text_input("Account Name *", value=_fd("account_name"), key="t_account_name")
        _save_fd("account_name", v)
        _gap_hint(gaps, "account_name")

        v = st.text_input("ARR", value=_fd("arr"), key="t_arr", placeholder="e.g. $250,000")
        _save_fd("arr", v)
    with c2:
        v = st.text_input("Region / Territory", value=_fd("region"), key="t_region")
        _save_fd("region", v)

        v = st.text_input("Renewal Date", value=_fd("renewal_date"), key="t_renewal_date",
                          placeholder="e.g. 2027-01-01")
        _save_fd("renewal_date", v)
    with c3:
        v = st.text_input("Contract Tier / Edition", value=_fd("contract_tier"), key="t_contract_tier")
        _save_fd("contract_tier", v)

        health_opts = ["", "🔴 Red", "🟡 Yellow", "🟢 Green"]
        current_health = _fd("health_score", "")
        health_idx = health_opts.index(current_health) if current_health in health_opts else 0
        v = st.selectbox("Account Health", health_opts, index=health_idx, key="t_health")
        _save_fd("health_score", v)

    c1, c2 = st.columns(2)
    with c1:
        v = st.text_input("Products / Modules in Use", value=_fd("products"), key="t_products")
        _save_fd("products", v)
    with c2:
        v = st.text_input("CSM Counterpart (if applicable)", value=_fd("csm_counterpart"), key="t_csm")
        _save_fd("csm_counterpart", v)

    st.divider()

    # Technical Environment
    st.subheader("Technical Environment")
    c1, c2 = st.columns(2)
    with c1:
        v = st.text_area("Tech Stack / Key Integrations", value=_fd("tech_stack"), key="t_tech_stack", height=80,
                         placeholder="e.g. Salesforce, AWS, Python-heavy, Snowflake data warehouse")
        _save_fd("tech_stack", v)
        _gap_hint(gaps, "tech_stack")

        v = st.text_input("Deployment Type", value=_fd("deployment"), key="t_deployment",
                          placeholder="e.g. Cloud (AWS us-east-1), On-prem, Hybrid")
        _save_fd("deployment", v)
    with c2:
        v = st.text_area("Scale / Usage", value=_fd("scale"), key="t_scale", height=80,
                         placeholder="e.g. 200 seats, ~50k API calls/day, 3 environments")
        _save_fd("scale", v)

        v = st.text_area("Known Technical Debt / Complexity", value=_fd("tech_debt"), key="t_tech_debt", height=80,
                         placeholder="Anything that makes this account technically complex or fragile")
        _save_fd("tech_debt", v)

    st.divider()

    # Stakeholders
    render_stakeholder_rows("t", gaps)
    st.divider()

    # In-Flight Work
    st.subheader("In-Flight Work")
    _gap_hint(gaps, "active_projects")
    v = st.text_area("Active Projects / POCs", value=_fd("active_projects"), key="t_active_projects", height=80,
                     placeholder="What is actively in-flight? Include status and owner.")
    _save_fd("active_projects", v)

    v = st.text_area("Open Escalations / Support Cases", value=_fd("escalations"), key="t_escalations", height=80,
                     placeholder="Ticket numbers, severity, current state")
    _save_fd("escalations", v)

    v = st.text_area("Pending Feature Requests / Workarounds", value=_fd("feature_requests"), key="t_feature_requests",
                     height=80, placeholder="FRs filed on their behalf, or workarounds currently in place")
    _save_fd("feature_requests", v)

    st.divider()

    # Product Gaps & Commitments
    st.subheader("Product Gaps & Commitments")
    v = st.text_area("Known Product Gaps", value=_fd("product_gaps"), key="t_product_gaps", height=80,
                     placeholder="Gaps the customer has hit — be specific about what's missing and the impact")
    _save_fd("product_gaps", v)

    v = st.text_area("Promises Made on Their Behalf", value=_fd("promises"), key="t_promises", height=80,
                     placeholder="Anything committed to this customer — roadmap items, workarounds, SLAs")
    _save_fd("promises", v)

    st.divider()

    # Red Flags
    render_red_flags("t", gaps)
    st.divider()

    # Key Dates
    st.subheader("Key Upcoming Dates")
    v = st.text_area("Known Upcoming Dates", value=_fd("key_dates"), key="t_key_dates", height=80,
                     placeholder="e.g. Renewal: Jan 2027 · QBR: June · Internal exec review: Aug")
    _save_fd("key_dates", v)
    st.divider()

    # Misc
    st.subheader("Additional Notes")
    v = st.text_area("Relationship nuances, political landmines, or anything not captured above",
                     value=_fd("misc_notes"), key="t_misc_notes", height=100)
    _save_fd("misc_notes", v)


def _handle_type_change_link():
    if st.button("Change handoff type", key="change_type_link"):
        st.session_state["handoff_type"] = None
        st.session_state.pop("form_data", None)
        st.session_state.pop("generated_output", None)
        st.session_state.pop("gaps", None)
        st.rerun()


# ── Gap detection + generation controls ───────────────────────────────────────

def render_action_bar(handoff_type: str):
    st.divider()
    gaps = st.session_state.get("gaps", [])

    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("Check for Gaps", use_container_width=True):
            with st.spinner("Checking..."):
                form_data = st.session_state.get("form_data", {})
                gaps = detect_gaps(handoff_type, form_data)
                st.session_state["gaps"] = gaps
            st.rerun()
    with col2:
        if st.button("Generate Handoff", type="primary", use_container_width=True):
            if not config.ANTHROPIC_API_KEY:
                st.error("Set ANTHROPIC_API_KEY in .env to generate handoffs.")
            else:
                form_data = st.session_state.get("form_data", {})
                st.session_state["generated_output"] = ""
                st.session_state["generating"] = True
                st.rerun()

    if gaps:
        errors = [g for g in gaps if g["severity"] == "error"]
        warnings = [g for g in gaps if g["severity"] == "warning"]
        summary_parts = []
        if errors:
            summary_parts.append(f"🔴 {len(errors)} critical")
        if warnings:
            summary_parts.append(f"🟡 {len(warnings)} warning{'s' if len(warnings) > 1 else ''}")
        st.caption(f"Gap check: {', '.join(summary_parts)} — see inline hints above")
    elif "gaps" in st.session_state:
        st.caption("✅ No gaps found")


# ── Output section ─────────────────────────────────────────────────────────────

def render_output_section(handoff_type: str):
    if st.session_state.get("generating"):
        st.divider()
        st.subheader("Generated Handoff")
        output_placeholder = st.empty()
        full_text = ""
        form_data = st.session_state.get("form_data", {})

        with output_placeholder.container():
            with st.spinner("Generating..."):
                for chunk in stream_handoff(handoff_type, form_data):
                    full_text += chunk
                    output_placeholder.markdown(full_text)

        st.session_state["generated_output"] = full_text
        st.session_state["generating"] = False
        st.rerun()

    output = st.session_state.get("generated_output", "")
    if not output:
        return

    st.divider()
    st.subheader("Generated Handoff")
    st.markdown(output)
    st.divider()

    account_name = st.session_state.get("form_data", {}).get("account_name", "Handoff")
    type_label = "Sales→CS" if handoff_type == "sales_to_cs" else "TAM→TAM"
    doc_title = f"{account_name} — {type_label} Handoff"

    col1, col2 = st.columns([1, 5])
    with col1:
        creds = get_credentials()
        if creds and not creds.expired:
            if st.button("Save to Google Drive", type="primary", use_container_width=True):
                with st.spinner("Saving to Google Drive..."):
                    try:
                        url = create_handoff_doc(creds, doc_title, output)
                        st.success(f"Saved! [Open in Google Docs]({url})")
                    except Exception as e:
                        st.error(f"Failed to save: {e}")
        else:
            st.info("Connect Google Drive in the sidebar to save this document.")

    with col2:
        if st.button("Download as Text", use_container_width=True):
            st.download_button(
                label="Download .txt",
                data=output,
                file_name=f"{doc_title}.txt",
                mime="text/plain",
            )


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    render_sidebar_header()
    render_sidebar_footer()

    _handle_oauth_callback()
    _handle_type_change_dialog()

    handoff_type = st.session_state.get("handoff_type")

    if not handoff_type:
        render_type_selection()
        return

    gaps = st.session_state.get("gaps", [])

    if handoff_type == "sales_to_cs":
        render_sales_to_cs_form(gaps)
    else:
        render_tam_to_tam_form(gaps)

    render_action_bar(handoff_type)
    render_output_section(handoff_type)


main()
