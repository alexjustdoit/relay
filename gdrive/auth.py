"""
Google OAuth 2.0 flow for Relay.

Flow:
  1. get_auth_url()       — build the Google authorization URL
  2. exchange_code()      — exchange the ?code= param for tokens
  3. load_tokens()        — load cached tokens from disk
  4. save_tokens()        — persist tokens to disk
  5. get_credentials()    — return valid google.oauth2.credentials.Credentials,
                            refreshing if needed
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow

import config

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
]

CLIENT_CONFIG = {
    "web": {
        "client_id": config.GOOGLE_CLIENT_ID,
        "client_secret": config.GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [config.GOOGLE_REDIRECT_URI],
    }
}


def _make_flow() -> Flow:
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
    flow.redirect_uri = config.GOOGLE_REDIRECT_URI
    return flow


def get_auth_url() -> str:
    flow = _make_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    st.session_state["oauth_state"] = state
    st.session_state["oauth_flow"] = flow  # preserve code_verifier for exchange
    return auth_url


def exchange_code(code: str) -> Credentials:
    # Reuse the stored flow so the code_verifier from PKCE is intact
    flow = st.session_state.pop("oauth_flow", None) or _make_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials
    save_tokens(creds)
    return creds


def save_tokens(creds: Credentials):
    try:
        config.TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        config.TOKEN_PATH.write_text(json.dumps({
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes) if creds.scopes else SCOPES,
        }))
    except OSError:
        pass  # Ephemeral filesystem (e.g. Streamlit Community Cloud) — session state is the only store


def load_tokens() -> Credentials | None:
    if not config.TOKEN_PATH.exists():
        return None
    try:
        data = json.loads(config.TOKEN_PATH.read_text())
        return Credentials(
            token=data["token"],
            refresh_token=data["refresh_token"],
            token_uri=data["token_uri"],
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            scopes=data["scopes"],
        )
    except Exception:
        return None


def get_credentials() -> Credentials | None:
    """Return valid credentials, refreshing if expired. Returns None if not authed."""
    creds = st.session_state.get("google_creds") or load_tokens()
    if not creds:
        return None
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_tokens(creds)
    st.session_state["google_creds"] = creds
    return creds


def revoke():
    """Clear stored credentials."""
    if config.TOKEN_PATH.exists():
        config.TOKEN_PATH.unlink()
    st.session_state.pop("google_creds", None)
