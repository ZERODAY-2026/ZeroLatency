"""Clause checklist page implementation.

Features:
- Two-column grouping: 'Wording found' vs 'No matching wording found'
- Neutral ink blue check icon for found; dashed neutral circle for not found (NO GREEN OR RED)
- Mandatory top disclaimer: 'Not found means the extracted text has no matching wording. It is not a legal conclusion.'
- Clickable page chips jumping directly to source viewer
- Safe HTML rendering with semantic rl-* classes
"""

import streamlit as st

from .components import render_empty_state, render_topbar
from .html import render_html, esc
from .icons import svg_icon
from .state import set_route
from .text import (
    CHECKLIST_FOUND_GROUP,
    CHECKLIST_NOT_FOUND_GROUP,
    CHECKLIST_SUBTITLE,
    CHECKLIST_TITLE,
)


def render_checklist() -> None:
    """Render the clause checklist comparison screen."""
    result = st.session_state.get("result")
    session = st.session_state.get("session")
    doc_name = st.session_state.get("doc_name", "document")

    render_topbar("Checklist", doc_name=doc_name, page_count=len(session.pages) if session else None)

    if result is None or session is None:
        render_empty_state("Clause checklist")
        return

    checklist = result.checklist
    found_items = [item for item in checklist if item.found]
    not_found_items = [item for item in checklist if not item.found]

    render_html(
        f"""
        <div style="margin-bottom:1.5rem;">
            <div class="rl-h1" style="font-size:28px; font-weight:600; color:var(--paper-primary);">{esc(CHECKLIST_TITLE)}</div>
            <div class="rl-callout" style="margin:0.75rem 0 1rem 0;">
                <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background-color:var(--ember); margin-top:5px; flex-shrink:0;"></span>
                <span>{esc(CHECKLIST_SUBTITLE)}</span>
            </div>
        </div>
        """
    )

    col_found, col_not_found = st.columns(2, gap="large")

    with col_found:
        render_html(
            f"""
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.75rem;">
                <span class="rl-card-title" style="font-size:18px; margin-bottom:0;">{esc(CHECKLIST_FOUND_GROUP)}</span>
                <span class="rl-badge rl-badge-verified" style="font-size:11px; height:20px; padding:0 0.5rem;">{len(found_items)}</span>
            </div>
            """
        )

        for idx, item in enumerate(found_items):
            pages_str = ", ".join(f"p. {p}" for p in item.pages)
            col_item_left, col_item_btn = st.columns([4, 1])
            with col_item_left:
                render_html(
                    f"""
                    <div style="padding:0.65rem 0.85rem; margin:0.25rem 0; border-radius:8px; background:var(--bg-surface); border:1px solid var(--line); display:flex; align-items:center; justify-content:space-between;">
                        <div style="display:flex; align-items:center; gap:0.6rem;">
                            <span style="color:var(--found);">{svg_icon("check_circle", 18, "var(--found)")}</span>
                            <span style="font-weight:600; font-size:13.5px; color:var(--paper-primary);">{esc(item.topic)}</span>
                        </div>
                        <span class="rl-mono" style="font-size:11px; padding:0.15rem 0.45rem; border-radius:4px; background:var(--bg-inset); border:1px solid var(--line); color:var(--paper-muted);">{pages_str}</span>
                    </div>
                    """
                )
            with col_item_btn:
                if item.pages and st.button("View", key=f"chk_found_{idx}", use_container_width=True):
                    st.session_state["viewer_page"] = item.pages[0]
                    st.session_state["viewer_quote"] = None
                    set_route("Findings")
                    st.rerun()

    with col_not_found:
        render_html(
            f"""
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.75rem;">
                <span class="rl-card-title" style="font-size:18px; margin-bottom:0;">{esc(CHECKLIST_NOT_FOUND_GROUP)}</span>
                <span class="rl-badge rl-badge-neutral" style="font-size:11px; height:20px; padding:0 0.5rem;">{len(not_found_items)}</span>
            </div>
            """
        )

        for item in not_found_items:
            render_html(
                f"""
                <div style="padding:0.65rem 0.85rem; margin:0.25rem 0; border-radius:8px; background:var(--bg-surface); border:1px solid var(--line); display:flex; align-items:center; gap:0.6rem;">
                    <span style="color:var(--paper-muted);">{svg_icon("info", 18, "var(--paper-muted)")}</span>
                    <span style="font-size:13.5px; color:var(--paper-secondary);">{esc(item.topic)}</span>
                </div>
                """
            )
