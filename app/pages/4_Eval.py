"""
Relay — Model Evaluation
Side-by-side comparison of generation models using demo scenarios.
"""
import sys
import time
from pathlib import Path

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
from data.demos import SALES_TO_CS_DEMOS, TAM_TO_TAM_DEMOS
from llm.generation import generate_handoff_sync

MODELS = [
    {"label": "claude-sonnet-4-6", "model": "claude-sonnet-4-6", "provider": "anthropic"},
    {"label": "gpt-5.4-mini",      "model": "gpt-5.4-mini",      "provider": "openai"},
    {"label": "gpt-5.4-nano",      "model": "gpt-5.4-nano",      "provider": "openai"},
]

st.markdown("## Model Eval")
st.caption("Generate the same scenario across all three models and compare output quality.")
st.divider()

# ── Scenario selector ──────────────────────────────────────────────────────────

col_type, col_scenario, col_run = st.columns([1.2, 2.5, 1])

with col_type:
    handoff_type = st.selectbox(
        "Handoff type",
        ["sales_to_cs", "tam_to_tam"],
        format_func=lambda x: "Sales → CS" if x == "sales_to_cs" else "TAM → TAM",
        key="eval_handoff_type",
    )

demos = SALES_TO_CS_DEMOS if handoff_type == "sales_to_cs" else TAM_TO_TAM_DEMOS

with col_scenario:
    scenario_name = st.selectbox("Scenario", list(demos.keys()), key="eval_scenario")

form_data = demos[scenario_name]

with col_run:
    st.markdown("&nbsp;", unsafe_allow_html=True)  # vertical alignment
    run = st.button("Run Eval", type="primary", use_container_width=True)

st.divider()

# ── Run ────────────────────────────────────────────────────────────────────────

cache_key = f"eval_results_{handoff_type}_{scenario_name}"

if run:
    st.session_state.pop(cache_key, None)
    results = {}
    for m in MODELS:
        with st.spinner(f"Generating with {m['label']}..."):
            t0 = time.time()
            try:
                text = generate_handoff_sync(handoff_type, form_data, m["model"], m["provider"])
                elapsed = time.time() - t0
                results[m["label"]] = {"text": text, "elapsed": elapsed, "error": None}
            except Exception as e:
                results[m["label"]] = {"text": "", "elapsed": 0, "error": str(e)}
    st.session_state[cache_key] = results
    st.rerun()

# ── Results ────────────────────────────────────────────────────────────────────

results = st.session_state.get(cache_key)

if not results:
    st.info("Select a scenario and click **Run Eval** to generate.")
    st.stop()

tabs = st.tabs([m["label"] for m in MODELS])
for tab, m in zip(tabs, MODELS):
    with tab:
        r = results.get(m["label"])
        if not r:
            st.warning("No result.")
            continue
        if r["error"]:
            st.error(f"Generation failed: {r['error']}")
            continue
        st.caption(f"Generated in {r['elapsed']:.1f}s")
        st.markdown(r["text"])
        st.divider()
        safe_name = scenario_name.replace("/", "-").replace("\\", "-")
        st.download_button(
            label="Download .txt",
            data=r["text"],
            file_name=f"{safe_name} — {m['label']}.txt",
            mime="text/plain",
            key=f"dl_{m['label']}",
            use_container_width=True,
        )
