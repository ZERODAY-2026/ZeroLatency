"""Main application entry point for Redline.

Initializes configuration, themes, sidebar navigation rail, and routes
between full-bleed landing pages (Home, Auth) and the core triage shell.
"""

import sys
from pathlib import Path
import streamlit as st

# Ensure backend package can be imported
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "private-legal-triage"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ui.desk import render_desk
from ui.rail import render_rail
from ui.state import get_active_theme, init_session_state, set_route
from ui.theme import inject_theme_css

from ui.html import render_html

# Page Configuration
st.set_page_config(
    page_title="Redline · Private Legal Triage",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
init_session_state()

# Route and Layout Determination
if hasattr(st, "query_params") and "route" in st.query_params:
    st.session_state["route"] = st.query_params["route"]

current_route = st.session_state.get("route", "Desk")
is_full_bleed = current_route in ("Home", "Auth")

# Inject Design System CSS
inject_theme_css(theme=get_active_theme(), is_full_bleed=is_full_bleed)

# Application Shell Routing
if current_route == "Home":
    try:
        from ui.home import render_home
        render_home()
    except ImportError:
        render_html('<div class="rl-card" style="padding:2rem; text-align:center;"><h1 class="rl-card-title">Redline</h1><p>Home view loading...</p></div>')
        if st.button("Go to Desk", key="home_fallback_desk"):
            set_route("Desk")
            st.rerun()

elif current_route == "Auth":
    try:
        from ui.auth import render_auth
        render_auth()
    except ImportError:
        render_html('<div class="rl-card" style="padding:2rem; text-align:center;"><h1 class="rl-card-title">Vault</h1><p>Vault lock loading...</p></div>')
        if st.button("Unlock to Desk", key="auth_fallback_desk"):
            st.session_state["auth_ok"] = True
            set_route("Desk")
            st.rerun()

else:
    # Standard shell with persistent left navigation rail
    render_rail()

    # Route within the results workspace
    status = st.session_state.get("status", "IDLE")

    if status == "ANALYZING":
        try:
            from ui.processing import render_processing
            render_processing()
        except ImportError:
            st.info("Analysis in progress...")
    elif current_route == "Desk":
        render_desk()
    elif current_route == "Overview":
        try:
            from ui.overview import render_overview
            render_overview()
        except ImportError:
            st.info("Overview page will load here once analysis completes.")
    elif current_route == "Findings":
        try:
            from ui.findings import render_findings
            render_findings()
        except ImportError:
            st.info("Findings page will load here.")
    elif current_route == "Ask":
        try:
            from ui.ask import render_ask
            render_ask()
        except ImportError:
            st.info("Ask page will load here.")
    elif current_route == "Key facts":
        try:
            from ui.facts import render_facts
            render_facts()
        except ImportError:
            st.info("Key facts page will load here.")
    elif current_route == "Checklist":
        try:
            from ui.checklist import render_checklist
            render_checklist()
        except ImportError:
            st.info("Checklist page will load here.")
    elif current_route == "Export":
        try:
            from ui.export import render_export
            render_export()
        except ImportError:
            st.info("Export page will load here.")
    elif current_route == "Privacy and model":
        try:
            from ui.privacy_page import render_privacy_page
            render_privacy_page()
        except ImportError:
            st.info("Privacy and model page will load here.")
