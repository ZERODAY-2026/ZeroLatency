"""Sticky source viewer component for PDF and TXT documents.

Features:
- PDF page image with highlighted passage via src.highlight.render_page
- TXT whitespace-tolerant text highlighter
- Fallback message when quote is verified but cannot be highlighted on page
- Page navigation: previous/next buttons and 'N of M' counter
- Accessible alt text and image captions
- Safe HTML rendering
"""

import html
import re
from pathlib import Path
from typing import Any
import streamlit as st

from src.highlight import render_page
from .html import render_html, esc


def render_source_viewer(
    doc_path: Path | str,
    total_pages: int,
    current_page: int = 1,
    highlight_quote: str | None = None,
    pages_data: list[Any] | None = None,
) -> None:
    """Render the sticky source viewer panel in the right column."""
    target_path = Path(doc_path)
    page_num = max(1, min(current_page, total_pages))

    # Header Controls (Prev, Next, Page Counter)
    col_hdr_left, col_hdr_right = st.columns([7, 5])
    with col_hdr_left:
        render_html(
            f"""
            <div style="display:flex; align-items:center; gap:0.5rem; padding-top:0.25rem;">
                <span class="rl-card-title" style="font-size:16px; margin-bottom:0;">Source viewer</span>
                <span style="font-size:12px; color:var(--paper-muted);">· Page {page_num} of {total_pages}</span>
            </div>
            """
        )
    with col_hdr_right:
        c_prev, c_cnt, c_next = st.columns([1, 2, 1])
        with c_prev:
            if st.button("‹", key="viewer_prev_btn", disabled=page_num <= 1, use_container_width=True):
                st.session_state["viewer_page"] = page_num - 1
                st.rerun()
        with c_cnt:
            render_html(
                f'<div class="rl-mono" style="text-align:center; font-size:13px; padding-top:0.4rem; color:var(--paper-secondary);">{page_num}/{total_pages}</div>'
            )
        with c_next:
            if st.button("›", key="viewer_next_btn", disabled=page_num >= total_pages, use_container_width=True):
                st.session_state["viewer_page"] = page_num + 1
                st.rerun()

    # Active passage caption
    if highlight_quote:
        render_html(
            f"""
            <div class="rl-chip" style="width:100%; margin:0.5rem 0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background-color:var(--marker); flex-shrink:0;"></span>
                <span class="rl-mono" style="font-size:11.5px; overflow:hidden; text-overflow:ellipsis;">Passage: "{esc(highlight_quote[:80])}..."</span>
            </div>
            """
        )

    # Document Content Rendering
    is_pdf = target_path.suffix.lower() == ".pdf"

    if is_pdf:
        # Render PDF via PyMuPDF highlight
        try:
            png_bytes = render_page(target_path, page_number=page_num, quote=highlight_quote, zoom=2.0)
            st.image(
                png_bytes,
                caption=f"Page {page_num} of {total_pages} (highlighted citations rendered locally)",
                use_container_width=True,
                output_format="PNG",
            )
        except Exception:
            # Fallback when highlight cannot be placed on page
            try:
                raw_bytes = render_page(target_path, page_number=page_num, quote=None, zoom=2.0)
                st.image(
                    raw_bytes,
                    caption=f"Page {page_num} of {total_pages}",
                    use_container_width=True,
                    output_format="PNG",
                )
                if highlight_quote:
                    st.info("The cited passage was verified in text but could not be visually highlighted on this page.")
            except Exception as e:
                st.error(f"Could not render page image: {e}")

    else:
        # Plain text rendering with tolerant <mark> highlight
        page_text = ""
        if pages_data and 0 <= page_num - 1 < len(pages_data):
            page_text = pages_data[page_num - 1].text

        if page_text:
            display_text = html.escape(page_text)
            if highlight_quote:
                clean_quote = re.sub(r"\s+", " ", highlight_quote.strip())
                pattern = re.compile(re.escape(clean_quote), re.IGNORECASE)
                display_text = pattern.sub(
                    lambda m: f'<mark style="background-color: rgba(247, 215, 72, 0.4); color: inherit; padding: 2px 4px; border-radius: 2px;">{m.group(0)}</mark>',
                    display_text,
                )

            render_html(
                f"""
                <div class="rl-mono" style="padding:1rem; background-color:var(--bg-inset); border:1px solid var(--line); border-radius:8px; font-size:13px; line-height:1.6; color:var(--paper-primary); max-height:600px; overflow-y:auto; white-space:pre-wrap; user-select:text;">
                    {display_text}
                </div>
                """
            )
        else:
            render_html(
                '<div style="padding:1rem; background-color:var(--bg-inset); border:1px solid var(--line); border-radius:8px; color:var(--paper-muted); font-size:13px;">No text on this page.</div>'
            )
