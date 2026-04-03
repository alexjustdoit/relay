"""
Relay — Technical Info (developer reference)
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

st.markdown("<style>[data-testid='stSidebarNav'],[data-testid='stSidebarNavItems'],[data-testid='stSidebarNavLink']{display:none!important}</style>", unsafe_allow_html=True)
import config  # noqa: F401

from llm import router

st.title("Technical Info")
st.caption("Developer reference — provider config, Ollama status, and environment variables.")
st.markdown("**Version:** 1.2.0")

# ── LLM Provider Architecture ──────────────────────────────────────────────────

st.subheader("LLM Provider Architecture")

import pandas as pd

provider_data = {
    "Provider": ["Ollama (local)", "OpenAI gpt-5.4-nano", "OpenAI gpt-5.4-mini", "Anthropic claude-sonnet-4-6"],
    "Cost": ["Free", "~$0.0004/call", "~$0.009/call", "~$0.030/call"],
    "Use Case": [
        "Development / zero API cost",
        "Gap detection — always used when on API (cheap, structured JSON task)",
        "Generation — default/testing mode",
        "Generation — high-quality mode (toggle on Technical Info page)",
    ],
}
st.dataframe(pd.DataFrame(provider_data), use_container_width=True, hide_index=True)

st.divider()

# ── Active Provider Config ─────────────────────────────────────────────────────

st.subheader("Active Provider Config")

col1, col2, col3 = st.columns(3)
with col1:
    mode = "Local (Ollama)" if router.is_local() else "API (OpenAI)"
    st.metric("Mode", mode)
with col2:
    st.metric("Gap Detection", router.gap_model())
with col3:
    st.metric("Generation", router.gen_model())

st.divider()

# ── Generation Quality Toggle ──────────────────────────────────────────────────

st.subheader("Generation Quality")
st.caption(
    "Controls which model is used for handoff narrative generation. "
    f"**Default: {config.HQ_MODEL}** — best output quality. "
    f"Switch to {config.MINI_MODEL} to cut costs during testing."
)

col_tog, col_info = st.columns([1, 3])
with col_tog:
    hq_on = os.getenv("USE_HIGH_QUALITY_GEN", "true").lower() == "true"
    use_hq = st.toggle(
        "High-quality generation",
        value=hq_on,
        help=f"On: {config.HQ_MODEL} (~$0.030/call)  ·  Off: {config.MINI_MODEL} (~$0.009/call)",
    )
    os.environ["USE_HIGH_QUALITY_GEN"] = "true" if use_hq else "false"
with col_info:
    if use_hq:
        st.success(f"**{config.HQ_MODEL}** active — default, best narrative quality.")
    else:
        st.info(f"**{config.MINI_MODEL}** active — testing mode, fast and cheap.")

st.divider()

# ── Google Drive ───────────────────────────────────────────────────────────────

st.subheader("Google Drive")

from gdrive.auth import get_credentials
creds = get_credentials()
gdrive_connected = creds is not None and not creds.expired

col_gd1, col_gd2, col_gd3 = st.columns(3)
with col_gd1:
    st.metric("OAuth Status", "Connected" if gdrive_connected else "Not signed in")
with col_gd2:
    st.metric("Handoffs Folder", "Relay Handoffs")
with col_gd3:
    st.metric("History File", "relay_history.json")

if gdrive_connected:
    st.success("Google Drive connected — exports save to the Relay Handoffs folder; history syncs across sessions.")
else:
    st.info("Not signed in. Sign in via the sidebar to enable Drive export and cross-session history.")

st.divider()

# ── Ollama Status ──────────────────────────────────────────────────────────────

st.subheader("Ollama")

ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

col1, col2 = st.columns([1, 2])
with col1:
    st.metric("Base URL", ollama_url)
with col2:
    st.metric("Model", ollama_model)

try:
    import httpx
    resp = httpx.get(f"{ollama_url}/api/tags", timeout=3.0)
    if resp.status_code == 200:
        tags = resp.json().get("models", [])
        pulled = [m["name"] for m in tags]
        if any(ollama_model in m for m in pulled):
            st.success(f"Ollama reachable · {ollama_model} is available")
        else:
            st.warning(
                f"Ollama reachable but **{ollama_model}** is not pulled. "
                f"Run: `ollama pull {ollama_model}`"
            )
        if pulled:
            with st.expander(f"All pulled models ({len(pulled)})"):
                st.write("  \n".join(f"• {m}" for m in pulled))
    else:
        st.error(f"Ollama responded with HTTP {resp.status_code}")
except Exception:
    st.error(f"Ollama not reachable at `{ollama_url}` — start Ollama or set OLLAMA_BASE_URL in .env")

st.divider()

# ── Environment Variables ──────────────────────────────────────────────────────

st.subheader("Environment Variables")


def _mask(val: str | None) -> str:
    if not val:
        return "—"
    if len(val) <= 8:
        return "***"
    return val[:4] + "***" + val[-4:]


env_rows = [
    {
        "Variable": "USE_LOCAL_LLM",
        "Value": os.getenv("USE_LOCAL_LLM", "false"),
        "Default": "false",
        "Description": "true → Ollama (free); false → OpenAI API",
    },
    {
        "Variable": "OPENAI_API_KEY",
        "Value": _mask(os.getenv("OPENAI_API_KEY")),
        "Default": "—",
        "Description": "Required for gap detection (gpt-5.4-nano) and testing-mode generation (gpt-5.4-mini)",
    },
    {
        "Variable": "ANTHROPIC_API_KEY",
        "Value": _mask(os.getenv("ANTHROPIC_API_KEY")),
        "Default": "—",
        "Description": "Required for high-quality generation (claude-sonnet-4-6)",
    },
    {
        "Variable": "OLLAMA_BASE_URL",
        "Value": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "Default": "http://localhost:11434",
        "Description": "Ollama API endpoint",
    },
    {
        "Variable": "OLLAMA_MODEL",
        "Value": os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
        "Default": "llama3.1:8b",
        "Description": "Model used when USE_LOCAL_LLM=true",
    },
    {
        "Variable": "GOOGLE_CLIENT_ID",
        "Value": _mask(os.getenv("GOOGLE_CLIENT_ID")),
        "Default": "—",
        "Description": "Google OAuth client ID (Drive + Docs API)",
    },
    {
        "Variable": "GOOGLE_CLIENT_SECRET",
        "Value": _mask(os.getenv("GOOGLE_CLIENT_SECRET")),
        "Default": "—",
        "Description": "Google OAuth client secret (required alongside client ID)",
    },
    {
        "Variable": "GOOGLE_REDIRECT_URI",
        "Value": os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501"),
        "Default": "http://localhost:8501",
        "Description": "Must match authorized URI in Google Cloud Console",
    },
]
st.dataframe(pd.DataFrame(env_rows), use_container_width=True, hide_index=True)

st.divider()

# ── Stack ──────────────────────────────────────────────────────────────────────

st.subheader("Stack")

import streamlit as _st

col1, col2 = st.columns(2)
with col1:
    st.metric("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
with col2:
    st.metric("Streamlit", _st.__version__)

st.divider()

# ── Links ──────────────────────────────────────────────────────────────────────

st.subheader("Links")
st.markdown("""
- [GitHub Repository](https://github.com/alexjustdoit/relay)
- [Ollama Model Library](https://ollama.com/library)
- [Google Cloud Console](https://console.cloud.google.com)
""")
