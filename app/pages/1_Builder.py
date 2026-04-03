"""
Relay — Handoff Builder page
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

st.markdown("<style>[data-testid='stSidebarNav'],[data-testid='stSidebarNavItems'],[data-testid='stSidebarNavLink']{display:none!important}</style>", unsafe_allow_html=True)

import config
from gdrive.auth import get_credentials
from gdrive.drive import create_handoff_doc
from llm.gap_detection import detect_gaps
from llm.generation import stream_handoff
from data.demos import SALES_TO_CS_DEMOS, TAM_TO_TAM_DEMOS
from data.store import save_draft, load_draft, clear_draft, save_to_history

st.markdown("""
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
.gap-error { color: #e74c3c; font-size: 0.85rem; }
.gap-warning { color: #f0a500; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

_TYPE_LABELS = {
    "sales_to_cs": "Sales → CS",
    "tam_to_tam": "TAM → TAM",
}


# ── Form helpers ───────────────────────────────────────────────────────────────

def _fd(key, default=""):
    return st.session_state.get("form_data", {}).get(key, default)


def _save_fd(key, value):
    if "form_data" not in st.session_state:
        st.session_state["form_data"] = {}
    st.session_state["form_data"][key] = value


def _key(name: str) -> str:
    """Return a versioned widget key so demo loads get fresh widget state."""
    v = st.session_state.get("_form_version", 0)
    return f"{name}_v{v}"


def _gap_hint(gaps: list[dict], field: str):
    target = field.lower().replace(" ", "_")
    for g in gaps:
        gfield = g.get("field", "").lower().replace(" ", "_").replace("-", "_")
        if gfield == target or target in gfield or gfield in target:
            icon = "🔴" if g["severity"] == "error" else "🟡"
            css = "gap-error" if g["severity"] == "error" else "gap-warning"
            st.markdown(f'<span class="{css}">{icon} {g["message"]}</span>', unsafe_allow_html=True)
            return


# ── Stakeholder rows ───────────────────────────────────────────────────────────

def render_stakeholder_rows(key_prefix: str, gaps: list):
    st.markdown("**Stakeholders**")
    _gap_hint(gaps, "stakeholders")
    if "stakeholders" not in st.session_state.get("form_data", {}):
        _save_fd("stakeholders", [{"name": "", "title": "", "role": "", "savviness": "", "sentiment": ""}])

    rows = _fd("stakeholders", [{"name": "", "title": "", "role": "", "savviness": "", "sentiment": ""}])
    updated = []
    has_gap = any("stakeholder" in g.get("field", "").lower() for g in gaps)

    for i, row in enumerate(rows):
        with st.expander(f"Stakeholder {i+1}" + (f" — {row['name']}" if row['name'] else ""), expanded=i == 0 or has_gap):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Name", value=row.get("name", ""), key=_key(f"{key_prefix}_sk_name_{i}"))
                title = st.text_input("Title", value=row.get("title", ""), key=_key(f"{key_prefix}_sk_title_{i}"))
                role = st.text_input("Role (e.g. Champion, Economic Buyer, Technical DRI)",
                                     value=row.get("role", ""), key=_key(f"{key_prefix}_sk_role_{i}"))
            with c2:
                savviness = st.text_area("Technical Savviness", value=row.get("savviness", ""),
                                         key=_key(f"{key_prefix}_sk_sav_{i}"), height=70,
                                         placeholder="e.g. Deep Python/cloud background, not hands-on with infra")
                sentiment = st.selectbox("Sentiment", ["", "Champion", "Positive", "Neutral", "Skeptical", "Detractor"],
                                         index=["", "Champion", "Positive", "Neutral", "Skeptical", "Detractor"].index(row.get("sentiment", "")),
                                         key=_key(f"{key_prefix}_sk_sent_{i}"))
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
    _gap_hint(gaps, "red_flags")
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
                               key=_key(f"{key_prefix}_flag_cat_{i}"))
        with c2:
            desc = st.text_area("Description", value=flag.get("description", ""),
                                key=_key(f"{key_prefix}_flag_desc_{i}"), height=80,
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


# ── Demo selector ──────────────────────────────────────────────────────────────

def render_demo_selector(handoff_type: str):
    demos = SALES_TO_CS_DEMOS if handoff_type == "sales_to_cs" else TAM_TO_TAM_DEMOS

    @st.dialog("Choose Demo Context")
    def _picker():
        st.caption("Select a scenario to pre-fill the form.")
        for name, data in demos.items():
            if st.button(name, use_container_width=True):
                st.session_state["form_data"] = dict(data)
                # Bump the form version so all widget keys change — this forces
                # Streamlit to use value= instead of cached widget state.
                st.session_state["_form_version"] = st.session_state.get("_form_version", 0) + 1
                st.session_state.pop("gaps", None)
                st.session_state.pop("gap_checked", None)
                st.session_state.pop("generated_output", None)
                st.rerun()

    @st.dialog("Clear form?")
    def _confirm_clear():
        st.markdown("All fields will be reset. This cannot be undone.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Clear form", use_container_width=True):
                clear_draft()
                st.session_state["_form_version"] = st.session_state.get("_form_version", 0) + 1
                st.session_state["form_data"] = {}
                for _k in ("generated_output", "gaps", "gap_checked", "generating"):
                    st.session_state.pop(_k, None)
                st.rerun()
        with c2:
            if st.button("Cancel", type="primary", use_container_width=True):
                st.rerun()

    @st.dialog("Change handoff type?")
    def _confirm_change_type():
        has_data = any(
            isinstance(v, str) and v.strip()
            for v in st.session_state.get("form_data", {}).values()
        )
        if has_data:
            st.markdown("You have unsaved progress. Changing type will clear all fields.")
        else:
            st.markdown("Return to handoff type selection?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Change type", use_container_width=True):
                _reset_to_type_selection()
                st.rerun()
        with c2:
            if st.button("Cancel", type="primary", use_container_width=True):
                st.rerun()

    _, col_change, col_start, col_demo = st.columns([2, 1.5, 1, 1])
    with col_change:
        if st.button("← Change Type", key=f"change_type_{handoff_type}", use_container_width=True):
            _confirm_change_type()
    with col_start:
        if st.button("Start Over", key=f"start_over_{handoff_type}", use_container_width=True):
            _confirm_clear()
    with col_demo:
        if st.button("Demo →", key=f"demo_btn_{handoff_type}", use_container_width=True,
                     help="Pre-fill the form with a sample handoff"):
            _picker()


# ── Sales → CS form ────────────────────────────────────────────────────────────

def render_sales_to_cs_form(gaps: list):
    st.markdown("## Sales → CS Handoff")
    render_demo_selector("sales_to_cs")
    st.divider()

    st.subheader("Account Overview")
    c1, c2 = st.columns(2)
    with c1:
        v = st.text_input("Account Name *", value=_fd("account_name"), key=_key("s_account_name"))
        _save_fd("account_name", v)
        _gap_hint(gaps, "account_name")

        v = st.text_input("Product / Plan", value=_fd("product"), key=_key("s_product"))
        _save_fd("product", v)
    with c2:
        v = st.text_input("ARR", value=_fd("arr"), key=_key("s_arr"), placeholder="e.g. $120,000")
        _save_fd("arr", v)

        v = st.text_input("Close Date", value=_fd("close_date"), key=_key("s_close_date"), placeholder="e.g. 2026-04-15")
        _save_fd("close_date", v)

    st.divider()

    st.subheader("Why They Bought")
    _gap_hint(gaps, "pain_points")
    v = st.text_area("Pain Points / Use Case", value=_fd("pain_points"), key=_key("s_pain_points"), height=150,
                     placeholder="What problem were they trying to solve? Why now?")
    _save_fd("pain_points", v)

    v = st.text_area("Success Criteria", value=_fd("success_criteria"), key=_key("s_success_criteria"), height=120,
                     placeholder="How will they measure success in the first 90 days?")
    _save_fd("success_criteria", v)
    _gap_hint(gaps, "success_criteria")

    v = st.text_area("Competitors Evaluated", value=_fd("competitors"), key=_key("s_competitors"), height=70,
                     placeholder="e.g. Considered Competitor A and B, went with us because of X")
    _save_fd("competitors", v)

    st.divider()
    render_stakeholder_rows("s", gaps)
    st.divider()

    st.subheader("Commitments & Promises")
    v = st.text_area("Written Commitments (in contract or email)", value=_fd("commitments_written"),
                     key=_key("s_comm_written"), height=120,
                     placeholder="e.g. Dedicated onboarding engineer for 60 days")
    _save_fd("commitments_written", v)

    v = st.text_area("Verbal / Unwritten Commitments", value=_fd("commitments_verbal"),
                     key=_key("s_comm_verbal"), height=120,
                     placeholder="Anything promised in calls that isn't in writing")
    _save_fd("commitments_verbal", v)

    v = st.text_area("Functionality Promises (things that don't exist yet)", value=_fd("commitments_functionality"),
                     key=_key("s_comm_func"), height=120,
                     placeholder="Features or capabilities promised that are on the roadmap or TBD")
    _save_fd("commitments_functionality", v)
    _gap_hint(gaps, "commitments")

    st.divider()
    render_red_flags("s", gaps)
    st.divider()

    st.subheader("Key Upcoming Dates")
    v = st.text_area("Known Upcoming Dates", value=_fd("key_dates"), key=_key("s_key_dates"), height=120,
                     label_visibility="collapsed",
                     placeholder="e.g. Go-live target: May 1 · Exec review: June · SKO: August")
    _save_fd("key_dates", v)
    st.divider()

    st.subheader("Additional Notes")
    v = st.text_area("Anything else the CSM should know?", value=_fd("misc_notes"), key=_key("s_misc_notes"), height=150)
    _save_fd("misc_notes", v)


# ── TAM → TAM form ─────────────────────────────────────────────────────────────

def render_tam_to_tam_form(gaps: list):
    st.markdown("## TAM → TAM Handoff")
    render_demo_selector("tam_to_tam")
    st.divider()

    st.subheader("Account Overview")
    c1, c2, c3 = st.columns(3)
    with c1:
        v = st.text_input("Account Name *", value=_fd("account_name"), key=_key("t_account_name"))
        _save_fd("account_name", v)
        _gap_hint(gaps, "account_name")

        v = st.text_input("ARR", value=_fd("arr"), key=_key("t_arr"), placeholder="e.g. $250,000")
        _save_fd("arr", v)
    with c2:
        v = st.text_input("Region / Territory", value=_fd("region"), key=_key("t_region"))
        _save_fd("region", v)

        v = st.text_input("Renewal Date", value=_fd("renewal_date"), key=_key("t_renewal_date"),
                          placeholder="e.g. 2027-01-01")
        _save_fd("renewal_date", v)
    with c3:
        v = st.text_input("Contract Tier / Edition", value=_fd("contract_tier"), key=_key("t_contract_tier"))
        _save_fd("contract_tier", v)

        health_opts = ["", "🔴 Red", "🟡 Yellow", "🟢 Green"]
        current_health = _fd("health_score", "")
        health_idx = health_opts.index(current_health) if current_health in health_opts else 0
        v = st.selectbox("Account Health", health_opts, index=health_idx, key=_key("t_health"))
        _save_fd("health_score", v)

    c1, c2 = st.columns(2)
    with c1:
        v = st.text_input("Products / Modules in Use", value=_fd("products"), key=_key("t_products"))
        _save_fd("products", v)
    with c2:
        v = st.text_input("CSM Counterpart (if applicable)", value=_fd("csm_counterpart"), key=_key("t_csm"))
        _save_fd("csm_counterpart", v)

    st.divider()

    st.subheader("Technical Environment")
    c1, c2 = st.columns(2)
    with c1:
        v = st.text_area("Tech Stack / Key Integrations", value=_fd("tech_stack"), key=_key("t_tech_stack"), height=80,
                         placeholder="e.g. Salesforce, AWS, Python-heavy, Snowflake data warehouse")
        _save_fd("tech_stack", v)
        _gap_hint(gaps, "tech_stack")

        v = st.text_input("Deployment Type", value=_fd("deployment"), key=_key("t_deployment"),
                          placeholder="e.g. Cloud (AWS us-east-1), On-prem, Hybrid")
        _save_fd("deployment", v)
    with c2:
        v = st.text_area("Scale / Usage", value=_fd("scale"), key=_key("t_scale"), height=80,
                         placeholder="e.g. 200 seats, ~50k API calls/day, 3 environments")
        _save_fd("scale", v)

        v = st.text_area("Known Technical Debt / Complexity", value=_fd("tech_debt"), key=_key("t_tech_debt"), height=80,
                         placeholder="Anything that makes this account technically complex or fragile")
        _save_fd("tech_debt", v)

    st.divider()
    render_stakeholder_rows("t", gaps)
    st.divider()

    st.subheader("In-Flight Work")
    _gap_hint(gaps, "active_projects")
    v = st.text_area("Active Projects / POCs", value=_fd("active_projects"), key=_key("t_active_projects"), height=80,
                     placeholder="What is actively in-flight? Include status and owner.")
    _save_fd("active_projects", v)

    v = st.text_area("Open Escalations / Support Cases", value=_fd("escalations"), key=_key("t_escalations"), height=80,
                     placeholder="Ticket numbers, severity, current state")
    _save_fd("escalations", v)

    v = st.text_area("Pending Feature Requests / Workarounds", value=_fd("feature_requests"), key=_key("t_feature_requests"),
                     height=80, placeholder="FRs filed on their behalf, or workarounds currently in place")
    _save_fd("feature_requests", v)

    st.divider()

    st.subheader("Product Gaps & Commitments")
    v = st.text_area("Known Product Gaps", value=_fd("product_gaps"), key=_key("t_product_gaps"), height=80,
                     placeholder="Gaps the customer has hit — be specific about what's missing and the impact")
    _save_fd("product_gaps", v)

    v = st.text_area("Promises Made on Their Behalf", value=_fd("promises"), key=_key("t_promises"), height=80,
                     placeholder="Anything committed to this customer — roadmap items, workarounds, SLAs")
    _save_fd("promises", v)

    st.divider()
    render_red_flags("t", gaps)
    st.divider()

    st.subheader("Key Upcoming Dates")
    v = st.text_area("Known Upcoming Dates", value=_fd("key_dates"), key=_key("t_key_dates"), height=120,
                     label_visibility="collapsed",
                     placeholder="e.g. Renewal: Jan 2027 · QBR: June · Internal exec review: Aug")
    _save_fd("key_dates", v)
    st.divider()

    st.subheader("Additional Notes")
    v = st.text_area("Relationship nuances, political landmines, or anything not captured above",
                     value=_fd("misc_notes"), key=_key("t_misc_notes"), height=150)
    _save_fd("misc_notes", v)


# ── Action bar ─────────────────────────────────────────────────────────────────

def render_action_bar(handoff_type: str):
    st.divider()
    gaps = st.session_state.get("gaps", [])

    # Auto-run gap check when triggered from the inline prompt
    if st.session_state.pop("_pending_gap_check", False):
        with st.spinner("Checking..."):
            gaps = detect_gaps(handoff_type, st.session_state.get("form_data", {}))
            st.session_state["gaps"] = gaps
            st.session_state["gap_checked"] = True
        st.rerun()

    col1, col2, col_spacer = st.columns([1.2, 1.8, 3])
    with col1:
        if st.button("Check for Gaps", use_container_width=True):
            with st.spinner("Checking..."):
                gaps = detect_gaps(handoff_type, st.session_state.get("form_data", {}))
                st.session_state["gaps"] = gaps
                st.session_state["gap_checked"] = True
            st.rerun()
    with col2:
        if st.button("Generate Handoff", type="primary", use_container_width=True):
            if not config.OPENAI_API_KEY:
                st.error("Set OPENAI_API_KEY in .env to generate handoffs.")
            elif not st.session_state.get("gap_checked"):
                st.session_state["_show_gap_prompt"] = True
                st.rerun()
            else:
                st.session_state["generated_output"] = ""
                st.session_state["generating"] = True
                st.rerun()

    # Inline gap check prompt — avoids modal overlay staying open during streaming
    if st.session_state.pop("_show_gap_prompt", False):
        st.warning(
            "You haven't run a gap check yet. It only takes a second and helps "
            "catch missing context before generating."
        )
        pc1, pc2, _ = st.columns([1.2, 1.8, 3])
        with pc1:
            if st.button("Check for Gaps", key="_gap_prompt_check", use_container_width=True):
                st.session_state["_pending_gap_check"] = True
                st.rerun()
        with pc2:
            if st.button("Generate Anyway", key="_gap_prompt_generate", type="primary", use_container_width=True):
                st.session_state["gap_checked"] = True
                st.session_state["generated_output"] = ""
                st.session_state["generating"] = True
                st.rerun()

    if gaps:
        errors = [g for g in gaps if g["severity"] == "error"]
        warnings = [g for g in gaps if g["severity"] == "warning"]
        parts = []
        if errors:
            parts.append(f"🔴 {len(errors)} critical")
        if warnings:
            parts.append(f"🟡 {len(warnings)} warning{'s' if len(warnings) > 1 else ''}")
        st.caption(f"Gap check: {', '.join(parts)} — see inline hints above")
    elif "gaps" in st.session_state:
        st.caption("✅ No gaps found")


from app.pdf_export import generate_pdf as _generate_pdf


# ── Output section ─────────────────────────────────────────────────────────────

def render_output_section(handoff_type: str):
    if st.session_state.get("generating"):
        st.divider()
        st.subheader("Generated Handoff")
        try:
            full_text = st.write_stream(
                stream_handoff(handoff_type, st.session_state.get("form_data", {}))
            )
        except Exception as e:
            st.error(f"Generation failed: {e}")
            st.session_state["generating"] = False
            return
        st.session_state["generated_output"] = full_text
        st.session_state["generating"] = False
        account_name = st.session_state.get("form_data", {}).get("account_name", "")
        save_to_history(handoff_type, account_name, full_text)
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

    safe_title = doc_title.replace("→", "-").replace("—", "-")

    col1, col2, col3 = st.columns([1, 1, 1])
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
            st.caption("Sign in with Google to export as a Google Doc.")
    with col2:
        st.download_button(
            label="Download .txt",
            data=output,
            file_name=f"{safe_title}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col3:
        try:
            pdf_bytes = _generate_pdf(output)
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=f"{safe_title}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.caption(f"PDF export unavailable: {e}")


# ── Type selection (shown when landing directly on Builder) ────────────────────

def render_type_selection():
    st.title("New Handoff")
    st.markdown("Choose the type of handoff you're creating.")
    st.markdown("")

    col1, col2, col_spacer = st.columns([1, 1, 2])

    with col1:
        st.markdown("""
        <div style="border:2px solid #333; border-radius:12px; padding:1.5rem; text-align:center; height:230px; display:flex; flex-direction:column; justify-content:center;">
            <div style="height:3.5rem; display:flex; align-items:center; justify-content:center; font-size:2.5rem; margin-bottom:0.75rem;">🤝</div>
            <div style="font-size:1.1rem; font-weight:700; margin-bottom:0.4rem;">Sales → CS</div>
            <div style="font-size:0.85rem; opacity:0.7; line-height:1.4;">Hand off a new customer from Sales to Customer Success</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")
        if st.button("Start Sales → CS", key="b_sales_to_cs", type="primary", use_container_width=True):
            st.session_state["_form_version"] = st.session_state.get("_form_version", 0) + 1
            st.session_state["handoff_type"] = "sales_to_cs"
            st.session_state["form_data"] = {}
            for _k in ("generated_output", "gaps", "gap_checked"):
                st.session_state.pop(_k, None)
            st.rerun()

    with col2:
        st.markdown("""
        <div style="border:2px solid #333; border-radius:12px; padding:1.5rem; text-align:center; height:230px; display:flex; flex-direction:column; justify-content:center;">
            <div style="height:3.5rem; display:flex; align-items:center; justify-content:center; font-size:2.5rem; margin-bottom:0.75rem;">🔄</div>
            <div style="font-size:1.1rem; font-weight:700; margin-bottom:0.4rem;">TAM → TAM</div>
            <div style="font-size:0.85rem; opacity:0.7; line-height:1.4;">Transfer an existing account between Technical Account Managers</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")
        if st.button("Start TAM → TAM", key="b_tam_to_tam", type="primary", use_container_width=True):
            st.session_state["_form_version"] = st.session_state.get("_form_version", 0) + 1
            st.session_state["handoff_type"] = "tam_to_tam"
            st.session_state["form_data"] = {}
            for _k in ("generated_output", "gaps", "gap_checked"):
                st.session_state.pop(_k, None)
            st.rerun()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _reset_to_type_selection():
    clear_draft()
    st.session_state["_form_version"] = st.session_state.get("_form_version", 0) + 1
    st.session_state["form_data"] = {}
    for _k in ("handoff_type", "generated_output", "gaps", "gap_checked", "generating"):
        st.session_state.pop(_k, None)


# ── Main ───────────────────────────────────────────────────────────────────────

handoff_type = st.session_state.get("handoff_type")

if not handoff_type:
    render_type_selection()
else:
    # Restore draft form data only after a genuine refresh (session state cleared
    # mid-fill). Explicit new-handoff starts set form_data={} so this is skipped.
    if "form_data" not in st.session_state:
        draft = load_draft()
        if draft and draft.get("handoff_type") == handoff_type:
            st.session_state["form_data"] = draft.get("form_data", {})

    gaps = st.session_state.get("gaps", [])
    if handoff_type == "sales_to_cs":
        render_sales_to_cs_form(gaps)
    else:
        render_tam_to_tam_form(gaps)

    # Auto-save draft after every render
    save_draft(handoff_type, st.session_state.get("form_data", {}))

    render_action_bar(handoff_type)
    render_output_section(handoff_type)
