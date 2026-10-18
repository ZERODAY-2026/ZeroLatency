"""Safe HTML rendering utility for Streamlit."""

import html
import textwrap
import streamlit as st


def esc(text: object) -> str:
    """HTML-escape dynamic user or document text safely without double-escaping."""
    if text is None:
        return ""
    val = str(text)
    # Check if already escaped to prevent &amp;amp;
    # Specifically unescape once then escape, or simply escape
    # But if val contains &amp; already from previous manual escaping, avoid double escape:
    # Actually, standard practice: unescape then escape to normalize:
    normalized = html.unescape(val)
    return html.escape(normalized, quote=True)


def render_html(html_str: str) -> None:
    """Safely render HTML without Streamlit markdown code-block triggers.
    
    Dedents, strips leading/trailing whitespace from each line,
    removes blank lines, and renders via st.html() (Streamlit 1.39+)
    or falls back to st.markdown(..., unsafe_allow_html=True).
    """
    if not html_str:
        return
    
    cleaned = textwrap.dedent(html_str)
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    collapsed = " ".join(lines)
    
    if hasattr(st, "html"):
        st.html(collapsed)
    else:
        st.markdown(collapsed, unsafe_allow_html=True)
