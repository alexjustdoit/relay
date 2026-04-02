"""
Central configuration. Reads from st.secrets (SCC) or .env (local).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


def _secret(key: str, default: str = "") -> str:
    """Read from st.secrets first (SCC), fall back to env."""
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


OPENAI_API_KEY: str = _secret("OPENAI_API_KEY")
GOOGLE_CLIENT_ID: str = _secret("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET: str = _secret("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI: str = _secret("GOOGLE_REDIRECT_URI", "http://localhost:8501")

NANO_MODEL: str = "gpt-5.4-nano"   # gap detection
MINI_MODEL: str = "gpt-5.4-mini"   # generation

TOKEN_PATH: Path = Path.home() / ".relay" / "tokens.json"
