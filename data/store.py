"""
Persistence layer for Relay.

Draft and history are stored in two places:
  1. st.session_state — always available, private per user, lost on refresh
  2. ~/.relay/*.json  — local only; silent fail on SCC (ephemeral filesystem)

On SCC, session state is the source of truth.
Locally, the file store persists across restarts.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

_BASE = Path.home() / ".relay"
_DRAFT_FILE = _BASE / "draft.json"
_HISTORY_FILE = _BASE / "history.json"
_MAX_HISTORY = 50


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


# ── Draft ──────────────────────────────────────────────────────────────────────

def save_draft(handoff_type: str, form_data: dict) -> None:
    draft = {"handoff_type": handoff_type, "form_data": form_data}
    st.session_state["_draft"] = draft
    _write(_DRAFT_FILE, draft)


def load_draft() -> dict | None:
    if "_draft" in st.session_state:
        return st.session_state["_draft"]
    data = _read(_DRAFT_FILE)
    if data:
        st.session_state["_draft"] = data
    return data


def clear_draft() -> None:
    st.session_state.pop("_draft", None)
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
    _write(_HISTORY_FILE, history)


def load_history() -> list:
    if "_history" in st.session_state:
        return st.session_state["_history"]
    data = _read(_HISTORY_FILE)
    if isinstance(data, list):
        st.session_state["_history"] = data
        return data
    st.session_state["_history"] = []
    return []


def delete_history_entry(entry_id: str) -> None:
    history = [e for e in load_history() if e["id"] != entry_id]
    st.session_state["_history"] = history
    _write(_HISTORY_FILE, history)


def clear_history() -> None:
    st.session_state["_history"] = []
    try:
        _HISTORY_FILE.unlink(missing_ok=True)
    except OSError:
        pass
