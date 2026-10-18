"""State management and session transitions for Redline.

Follows the state machine in frontend.md (section 8) and DESIGN.md:
IDLE -> READY -> ANALYZING -> DONE (or ERROR from any step)
"""

import sys
from pathlib import Path
from typing import Any, Literal
import streamlit as st

# Add private-legal-triage to sys.path so src imports resolve cleanly
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "private-legal-triage"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.config import settings
from src.gemma_client import OllamaClient
from src.pipeline import DocumentSession
from src.privacy import PrivateWorkspace, network_guard

Status = Literal["IDLE", "READY", "ANALYZING", "DONE", "ERROR"]
Route = Literal[
    "Home",
    "Auth",
    "Desk",
    "Overview",
    "Findings",
    "Ask",
    "Key facts",
    "Checklist",
    "Export",
    "Privacy and model",
]

DEFAULT_STATE: dict[str, Any] = {
    # Core frontend.md keys
    "status": "IDLE",
    "workspace": None,  # PrivateWorkspace instance
    "path": None,  # Path to document in PrivateWorkspace
    "doc_name": None,  # Original uploaded file name
    "session": None,  # DocumentSession instance
    "result": None,  # TriageResult instance
    "answers": [],  # list of Answer instances
    "selected_finding": None,  # currently active Finding
    "viewer_page": 1,  # currently viewed source page number
    "viewer_quote": None,  # quote to highlight in viewer
    "blocked_hosts": [],  # observed blocked outbound hosts
    "error": None,  # error tuple: (exception_class_name, exception_str)
    "ready_checked": False,  # whether Ollama readiness check has run
    "ready_status": None,  # (is_ready, message, command)
    # UI Navigation & Theme
    "route": "Desk",
    "theme": "dark",  # "dark" (Ink Room) or "light" (Paper Room)
    "auth_ok": False,  # true if vault unlocked or not configured
    "vault_enabled": False,  # true if local passphrase was configured
    "vault_hash": None,  # scrypt/pbkdf2 hash of passphrase
    "vault_salt": None,  # salt for passphrase
    "shred_triggered": False,  # triggers shred animation before wipe
    "analysis_progress": (0, 0),  # (current_chunk, total_chunks)
    "analysis_start_time": 0.0,
    "selected_category": "All",
    "selected_type": "All",
    "selected_verification": "All",
    "selected_confidence": "All",
    "filter_needs_review": False,
    "search_query": "",
    "sort_order": "Page order",
}


def init_session_state() -> None:
    """Initialize all session keys if not already present."""
    for key, val in DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = val


def get_active_theme() -> str:
    """Return 'dark' or 'light'."""
    return st.session_state.get("theme", "dark")


def toggle_theme() -> None:
    """Toggle between Ink Room (dark) and Paper Room (light)."""
    current = st.session_state.get("theme", "dark")
    st.session_state["theme"] = "light" if current == "dark" else "dark"


def set_route(route: Route) -> None:
    """Change the active destination route."""
    st.session_state["route"] = route
    try:
        if hasattr(st, "query_params"):
            st.query_params["route"] = route
    except Exception:
        pass


def clear_session() -> None:
    """Wipe temp workspace, clear in-memory state, and return to Desk or Home."""
    workspace = st.session_state.get("workspace")
    if workspace is not None:
        try:
            workspace.cleanup()
        except Exception:
            pass

    # Retain app settings (theme, vault settings)
    preserved = {
        "theme": st.session_state.get("theme", "dark"),
        "vault_enabled": st.session_state.get("vault_enabled", False),
        "vault_hash": st.session_state.get("vault_hash"),
        "vault_salt": st.session_state.get("vault_salt"),
        "auth_ok": st.session_state.get("auth_ok", False),
        "route": "Desk",
    }

    st.session_state.clear()
    init_session_state()
    for k, v in preserved.items():
        st.session_state[k] = v


def check_ollama_readiness(force: bool = False) -> tuple[bool, str, str | None]:
    """Check Ollama availability and model installation once per session or on demand."""
    if st.session_state.get("ready_checked") and not force:
        return st.session_state.get("ready_status", (False, "Checking...", None))

    client = OllamaClient(settings)
    observed: list[str] = []
    try:
        with network_guard(observed):
            client.check_ready()
            st.session_state["ready_checked"] = True
            st.session_state["ready_status"] = (True, "Local model ready", None)
            return (True, "Local model ready", None)
    except Exception as exc:
        cls_name = exc.__class__.__name__
        msg = str(exc)
        cmd = getattr(exc, "command", None)
        if cls_name == "OllamaUnavailable":
            msg = "The local model isn't running."
            cmd = "ollama serve"
        elif cls_name == "ModelMissing":
            msg = f"The model isn't installed. Run: ollama pull {settings.model}"
            cmd = f"ollama pull {settings.model}"
        st.session_state["ready_checked"] = True
        st.session_state["ready_status"] = (False, msg, cmd)
        return (False, msg, cmd)
