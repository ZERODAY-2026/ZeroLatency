"""Key facts table implementation.

Features:
- Structured table of amounts, dates, durations, and percentages
- Mono values and verbatim extracted snippets
- 'View' action that opens the source viewer with the cited snippet highlighted
- Filter controls
- Safe HTML rendering with semantic rl-* classes
"""

import streamlit as st

from .components import render_empty_state, render_topbar
from .html import render_html, esc
from .state import set_route
from .text import KEY_FACTS_EMPTY, KEY_FACTS_SUBTITLE, KEY_FACTS_TITLE


def render_facts() -> None:
    """Render the Key facts table screen."""
    result = st.session_state.get("result")
    session = st.session_state.get("session")
    doc_name = st.session_state.get("doc_name", "document")

    render_topbar("Key facts", doc_name=doc_name, page_count=len(session.pages) if session else None)

    if result is None or session is None:
        render_empty_state("Key facts")
        return

    facts = result.key_facts

    render_html(
        f"""
        <div style="margin-bottom:1.5rem;">
            <div class="rl-h1" style="font-size:28px; font-weight:600; color:var(--paper-primary);">{esc(KEY_FACTS_TITLE)}</div>
            <div style="font-size:13px; color:var(--paper-secondary); margin-top:0.25rem;">{esc(KEY_FACTS_SUBTITLE)}</div>
        </div>
        """
    )

    if not facts:
        render_html(f'<div class="rl-card" style="text-align:center; padding:2.5rem; color:var(--paper-muted); font-size:14px;">{esc(KEY_FACTS_EMPTY)}</div>')
        return

    # Search and Filter Bar
    col_search, col_filter = st.columns([4, 2])
    with col_search:
        fact_search = st.text_input("Search facts", placeholder="Search label or value...", label_visibility="collapsed")
    with col_filter:
        fact_type = st.selectbox("Type", options=["All", "Amount", "Date", "Duration", "Percentage"], label_visibility="collapsed")

    filtered_facts = []
    for f in facts:
        if fact_search:
            sq = fact_search.lower()
            if sq not in f.label.lower() and sq not in f.value.lower() and sq not in f.snippet.lower():
                continue
        filtered_facts.append(f)

    # Render Table Header
    render_html(
        """
        <div style="padding:0.6rem 0.75rem; background:var(--bg-inset); border:1px solid var(--line); border-radius:8px 8px 0 0; margin-bottom:-1px;">
            <div style="display:grid; grid-template-columns: 3fr 3fr 1fr 4fr 1fr; gap:0.75rem; font-size:11px; font-weight:600; color:var(--paper-muted); text-transform:uppercase; letter-spacing:0.05em;">
                <div>Fact Label</div>
                <div>Extracted Value</div>
                <div style="text-align:center;">Page</div>
                <div>Cited Passage Snippet</div>
                <div style="text-align:right;">Action</div>
            </div>
        </div>
        """
    )

    # Render Table Rows
    for idx, fact in enumerate(filtered_facts):
        col_lbl, col_val, col_pg, col_snip, col_act = st.columns([3, 3, 1, 4, 1])
        with col_lbl:
            render_html(f'<div style="font-weight:600; font-size:13.5px; color:var(--paper-primary); padding-top:0.5rem;">{esc(fact.label)}</div>')
        with col_val:
            render_html(f'<div class="rl-mono" style="font-size:13px; color:var(--paper-primary); font-weight:600; padding-top:0.5rem;">{esc(fact.value)}</div>')
        with col_pg:
            render_html(f'<div class="rl-mono" style="font-size:12px; color:var(--paper-muted); text-align:center; padding-top:0.5rem;">p. {fact.page}</div>')
        with col_snip:
            render_html(f'<div class="rl-mono" style="font-size:12px; color:var(--paper-secondary); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; padding-top:0.5rem;" title="{esc(fact.snippet)}">"{esc(fact.snippet)}"</div>')
        with col_act:
            if st.button("View", key=f"fact_view_{idx}", use_container_width=True):
                st.session_state["viewer_page"] = fact.page
                st.session_state["viewer_quote"] = fact.snippet
                set_route("Findings")
                st.rerun()
