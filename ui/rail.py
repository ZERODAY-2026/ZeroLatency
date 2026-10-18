"""Persistent Navigation Sidebar for Redline.

Fixed width ~272px, expanded by default.
All eight destinations are always unlocked with active indicators.
Uses native Streamlit Material icons and safe semantic rl-* HTML components.
"""

from html import escape
import streamlit as st

from .html import render_html, esc
from .state import clear_session, get_active_theme, set_route, toggle_theme
from .text import (
    AIRGAP_BADGE_SUB,
    AIRGAP_BADGE_TITLE,
    APP_NAME,
    APP_TAGLINE,
    CLEAR_SESSION_TITLE,
    DISCLAIMER_SHORT,
)


NAV_ITEMS = [
    ("Desk", ":material/folder:"),
    ("Overview", ":material/dashboard:"),
    ("Findings", ":material/search:"),
    ("Ask", ":material/chat:"),
    ("Key facts", ":material/table_rows:"),
    ("Checklist", ":material/checklist:"),
    ("Export", ":material/download:"),
    ("Privacy and model", ":material/shield_person:"),
]


def render_rail() -> None:
    """Render the unclipped 272px navigation sidebar."""
    with st.sidebar:
        current_route = st.session_state.get("route", "Desk")
        theme = get_active_theme()
        result = st.session_state.get("result")
        doc_name = st.session_state.get("doc_name")
        session = st.session_state.get("session")
        page_count = len(session.pages) if session and session.pages else 0

        theme_label = "Paper Room (Light)" if theme == "dark" else "Ink Room (Dark)"
        theme_icon = ":material/light_mode:" if theme == "dark" else ":material/dark_mode:"

        # 1. Brand Header (Clicking Logo/Brand goes to Home)
        col_brand_icon, col_brand_text = st.columns([1, 4])
        with col_brand_icon:
            if st.button("⚖️", key="nav_brand_icon", help="Return to Home"):
                set_route("Home")
                st.rerun()
        with col_brand_text:
            render_html(
                f"""
                <div style="cursor: pointer; padding-top: 2px;">
                    <div class="rl-sidebar-brand-title">{esc(APP_NAME)}</div>
                    <div class="rl-sidebar-brand-sub">{esc(APP_TAGLINE)}</div>
                </div>
                """
            )

        # 2. Privacy Badge (Local only)
        render_html(
            f"""
            <div class="rl-sidebar-badge">
                <span style="display:inline-block; width:7px; height:7px; border-radius:50%; background-color:var(--local-teal);" class="anim-breathing-dot"></span>
                <div>
                    <div style="font-weight:600; color:var(--local-teal);">{esc(AIRGAP_BADGE_TITLE)}</div>
                    <div style="color:var(--paper-muted); font-size:10px;">{esc(AIRGAP_BADGE_SUB)}</div>
                </div>
            </div>
            """
        )

        # 3. Document Chip
        if doc_name:
            doc_label = f"📄 {doc_name}"
            if page_count:
                doc_label += f" ({page_count}p)"
            render_html(
                f"""
                <div class="rl-sidebar-doc" title="{esc(doc_label)}">
                    {esc(doc_label)}
                </div>
                """
            )
        else:
            render_html(
                """
                <div class="rl-sidebar-doc" style="color:var(--paper-muted);">
                    📄 No document loaded
                </div>
                """
            )

        # 4. Navigation items (All 8 destinations always unlocked)
        for label, icon in NAV_ITEMS:
            is_active = current_route == label
            btn_key = f"nav_{label.lower().replace(' ', '_')}"
            btn_type = "primary" if is_active else "secondary"

            # Count / hint badge for populated views
            display_label = label
            if label == "Findings" and result and result.findings:
                display_label = f"{label} ({len(result.findings)})"
            elif label == "Key facts" and result and result.key_facts:
                display_label = f"{label} ({len(result.key_facts)})"
            elif label == "Checklist" and result and result.checklist:
                display_label = f"{label} ({len(result.checklist)})"

            if st.button(
                label=display_label,
                key=btn_key,
                icon=icon,
                type=btn_type,
                use_container_width=True,
            ):
                if current_route != label:
                    set_route(label)
                    st.rerun()

        # Spacer
        render_html('<div style="height: 1.25rem;"></div>')

        # 5. Model line
        render_html(
            """
            <div style="font-size:11px; color:var(--paper-muted); line-height:1.4; padding:0 0.25rem 0.5rem 0.25rem;">
                <span class="rl-mono" style="color:var(--paper-secondary); font-weight:600;">Model: gemma3n:e2b</span><br/>
                Runs locally via Ollama on this device
            </div>
            """
        )

        # 6. Theme toggle
        if st.button(
            label=f"Switch to {theme_label}",
            key="rail_theme_toggle",
            icon=theme_icon,
            use_container_width=True,
        ):
            toggle_theme()
            st.rerun()

        # 7. Clear and start over popover
        with st.popover(f"🗑️ {CLEAR_SESSION_TITLE}", use_container_width=True):
            render_html(
                """
                <p class="rl-card-sub">
                    This deletes the document and every result from this session. It cannot be undone.
                </p>
                """
            )
            col_del, col_cancel = st.columns(2)
            with col_del:
                if st.button("Delete", key="rail_confirm_clear", type="primary", use_container_width=True):
                    clear_session()
                    st.toast("Session cleared. Temporary files deleted.")
                    set_route("Desk")
                    st.rerun()
            with col_cancel:
                st.button("Cancel", key="rail_cancel_clear", use_container_width=True)

        # 8. Short disclaimer
        render_html(
            f"""
            <div class="rl-disclaimer">
                {esc(DISCLAIMER_SHORT)}
            </div>
            """
        )
