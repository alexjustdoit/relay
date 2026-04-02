"""
Google OAuth 2.0 flow for Relay.

Flow:
  1. get_auth_url()       — build the Google authorization URL (no PKCE)
  2. exchange_code()      — exchange the ?code= param for tokens via direct POST
  3. load_tokens()        — load cached tokens from disk
  4. save_tokens()        — persist tokens to disk
  5. get_credentials()    — return valid google.oauth2.credentials.Credentials,
                            refreshing if needed

Token exchange is done with a direct requests.post() instead of google-auth-oauthlib's
Flow.fetch_token(), which adds PKCE automatically in newer versions. PKCE requires the
code_verifier to survive the OAuth redirect, but Streamlit Community Cloud starts a fresh
session on redirect — making the stored verifier unavailable.
"""
import json
import sys
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import streamlit as st
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

import config

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
]

_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
_TOKEN_URI = "https://oauth2.googleapis.com/token"


def get_auth_url() -> str:
    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{_AUTH_URI}?{urlencode(params)}"


def exchange_code(code: str) -> Credentials:
    resp = requests.post(_TOKEN_URI, data={
        "client_id": config.GOOGLE_CLIENT_ID,
        "client_secret": config.GOOGLE_CLIENT_SECRET,
        "code": code,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    })
    if not resp.ok:
        try:
            detail = resp.json()
            error = detail.get("error", resp.status_code)
            description = detail.get("error_description", "")
            raise ValueError(f"{error}: {description}" if description else str(error))
        except (KeyError, ValueError) as e:
            raise ValueError(str(e)) from None
    token_data = resp.json()

    creds = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=_TOKEN_URI,
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )
    save_tokens(creds)
    st.session_state["google_creds"] = creds
    return creds


def save_tokens(creds: Credentials):
    try:
        config.TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        config.TOKEN_PATH.write_text(json.dumps({
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": _TOKEN_URI,
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "scopes": SCOPES,
        }))
    except OSError:
        pass  # Ephemeral filesystem (SCC) — session state is the only store


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
