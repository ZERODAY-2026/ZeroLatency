"""Report export page implementation.

Features:
- Report preview rendered in styled paper container
- 'What's inside' content checklist
- Verification disclaimer repeated prominently
- In-memory download button building Markdown report via src.report.to_markdown
- Safe HTML rendering with semantic rl-* classes
"""

import streamlit as st

from src.report import to_markdown

from .components import render_empty_state, render_topbar
from .html import render_html, esc
from .icons import svg_icon
from .text import (
    EXPORT_CAVEAT,
    EXPORT_DOWNLOAD_BTN,
    EXPORT_INSIDE_ITEMS,
    EXPORT_INSIDE_TITLE,
    EXPORT_SUBTITLE,
    EXPORT_TITLE,
)


def render_export() -> None:
    """Render the export report screen."""
    result = st.session_state.get("result")
    session = st.session_state.get("session")
    answers = st.session_state.get("answers", [])
    doc_name = st.session_state.get("doc_name", "document")

    render_topbar("Export", doc_name=doc_name, page_count=len(session.pages) if session else None)

    if result is None:
        render_empty_state("Export report")
        return

    # Generate Markdown report in memory
    report_md = to_markdown(result, answers)
    download_filename = f"triage_report_{doc_name.replace('.pdf', '').replace('.txt', '')}.md"

    render_html(
        f"""
        <div style="margin-bottom:1.5rem;">
            <div class="rl-h1" style="font-size:28px; font-weight:600; color:var(--paper-primary);">{esc(EXPORT_TITLE)}</div>
            <div style="font-size:13px; color:var(--paper-secondary); margin-top:0.25rem;">{esc(EXPORT_SUBTITLE)}</div>
        </div>
        """
    )

    col_preview, col_info = st.columns([7, 5], gap="large")

    with col_preview:
        render_html(
            f"""
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:0.5rem;">
                <span class="rl-card-title" style="font-size:16px; margin-bottom:0;">Report preview</span>
                <span class="rl-mono" style="font-size:11px; color:var(--paper-muted);">Markdown format</span>
            </div>
            <div class="rl-mono" style="padding:1.25rem; background:var(--bg-inset); border:1px solid var(--line); border-radius:10px; font-size:12px; line-height:1.6; color:var(--paper-primary); max-height:560px; overflow-y:auto; user-select:text; white-space:pre-wrap;">
                {esc(report_md)}
            </div>
            """
        )

    with col_info:
        # What's inside card
        items_html = "".join(
            f'<div style="display:flex; align-items:center; gap:0.5rem; font-size:13px; color:var(--paper-secondary); padding:0.4rem 0; border-bottom:1px solid var(--line);">{svg_icon("check", 14, "var(--found)")} <span>{esc(item)}</span></div>'
            for item in EXPORT_INSIDE_ITEMS
        )

        render_html(
            f"""
            <div class="rl-card">
                <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.75rem;">
                    {svg_icon("description", 18, "var(--paper-primary)")}
                    <span class="rl-card-title" style="font-size:16px; margin-bottom:0;">{esc(EXPORT_INSIDE_TITLE)}</span>
                </div>
                <div>
                    {items_html}
                </div>
                <div class="rl-callout" style="margin-top:1rem; font-size:12px;">
                    {esc(EXPORT_CAVEAT)}
                </div>
            </div>
            """
        )

        # Primary Download Button
        st.download_button(
            label=f"💾 {EXPORT_DOWNLOAD_BTN}",
            data=report_md,
            file_name=download_filename,
            mime="text/markdown",
            type="primary",
            use_container_width=True,
            key="export_download_btn",
        )
