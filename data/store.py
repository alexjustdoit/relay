"""
Persistence layer for Relay.

Draft and history are stored in three places (priority order):
  1. st.session_state  — always available, private per user, lost on refresh
  2. browser localStorage — survives refresh, browser-local, works on SCC
  3. ~/.relay/*.json   — local only; silent fail on SCC (ephemeral filesystem)

On SCC, session state + localStorage are the sources of truth.
Locally, the file store also persists across restarts.
"""
import base64
import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

_BASE = Path.home() / ".relay"
_DRAFT_FILE = _BASE / "draft.json"
_HISTORY_FILE = _BASE / "history.json"
_MAX_HISTORY = 50

_LS_DRAFT = "relay_draft"
_LS_HISTORY = "relay_history"


# ── File I/O ───────────────────────────────────────────────────────────────────

def _write(path: Path, data) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
    except OSError:
        pass


def _read(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


# ── localStorage I/O ───────────────────────────────────────────────────────────

def _ls_write(key: str, data) -> None:
    """Write data to browser localStorage via base64 to avoid quote issues."""
    try:
        from streamlit_javascript import st_javascript
        b64 = base64.b64encode(json.dumps(data).encode()).decode()
        st_javascript(f"localStorage.setItem('{key}', atob('{b64}'))")
    except Exception:
        pass


def _ls_read(key: str):
    """
    Read data from browser localStorage.
    Returns None on the very first render (async); the page reruns and
    picks up the real value on the second pass.
    """
    try:
        from streamlit_javascript import st_javascript
        raw = st_javascript(f"localStorage.getItem('{key}')")
        if isinstance(raw, str) and raw:
            return json.loads(raw)
    except Exception:
        pass
    return None


def _ls_remove(key: str) -> None:
    try:
        from streamlit_javascript import st_javascript
        st_javascript(f"localStorage.removeItem('{key}')")
    except Exception:
        pass


# ── Draft ──────────────────────────────────────────────────────────────────────

def save_draft(handoff_type: str, form_data: dict) -> None:
    draft = {"handoff_type": handoff_type, "form_data": form_data}
    st.session_state["_draft"] = draft
    _ls_write(_LS_DRAFT, draft)
    _write(_DRAFT_FILE, draft)


def load_draft() -> dict | None:
    if "_draft" in st.session_state:
        return st.session_state["_draft"]
    # Try localStorage (survives refresh on SCC), then file (local only)
    data = _ls_read(_LS_DRAFT) or _read(_DRAFT_FILE)
    if data:
        st.session_state["_draft"] = data
    return data


def clear_draft() -> None:
    st.session_state.pop("_draft", None)
    _ls_remove(_LS_DRAFT)
    try:
        _DRAFT_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def has_draft() -> bool:
    return load_draft() is not None


# ── History ────────────────────────────────────────────────────────────────────

def save_to_history(handoff_type: str, account_name: str, output: str) -> None:
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "handoff_type": handoff_type,
        "account_name": account_name or "Unnamed Account",
        "output": output,
    }
    history = load_history()
    history.insert(0, entry)
    history = history[:_MAX_HISTORY]
    st.session_state["_history"] = history
    _ls_write(_LS_HISTORY, history)
    _write(_HISTORY_FILE, history)


def load_history() -> list:
    if "_history" in st.session_state:
        return st.session_state["_history"]
    # Try localStorage (survives refresh on SCC), then file (local only)
    data = _ls_read(_LS_HISTORY) or _read(_HISTORY_FILE)
    if isinstance(data, list):
        st.session_state["_history"] = data
        return data
    st.session_state["_history"] = []
    return []


def delete_history_entry(entry_id: str) -> None:
    history = [e for e in load_history() if e["id"] != entry_id]
    st.session_state["_history"] = history
    _ls_write(_LS_HISTORY, history)
    _write(_HISTORY_FILE, history)


def clear_history() -> None:
    st.session_state["_history"] = []
    _ls_remove(_LS_HISTORY)
    try:
        _HISTORY_FILE.unlink(missing_ok=True)
    except OSError:
        pass
