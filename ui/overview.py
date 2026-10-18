"""Overview page implementation.

Features:
- 'Preliminary overview' summary card with interpretation caveat note
- Counts by category with horizontal progress bars
- 'Needs professional review' shortlist linking directly to findings
- Prompt-injection security notice if present
- Limitations expander (open by default)
- Full triage disclaimer with escalation advice
"""

import streamlit as st

from .components import (
    render_disclaimer,
    render_empty_state,
    render_results_header,
    render_topbar,
)
from .html import render_html, esc
from .icons import svg_icon
from .state import set_route


def render_overview() -> None:
    """Render the Overview screen."""
    result = st.session_state.get("result")
    session = st.session_state.get("session")
    doc_name = st.session_state.get("doc_name", "document")

    render_topbar("Overview", doc_name=doc_name, page_count=len(session.pages) if session else None)

    if result is None or session is None:
        render_empty_state("Overview")
        return

    findings = result.findings

    # 1. Header Strip
    verified_count = sum(1 for f in findings if f.verification_status == "verified")
    review_count = sum(1 for f in findings if f.needs_human_review)
    render_results_header(
        doc_name=doc_name,
        findings_count=len(findings),
        verified_count=verified_count,
        review_count=review_count,
        elapsed_seconds=result.elapsed_seconds,
    )

    render_html(
        """
        <div style="margin-bottom:1.5rem;">
            <div class="rl-h1" style="font-size:28px; font-weight:600; color:var(--paper-primary);">Preliminary overview</div>
            <div style="font-size:13px; color:var(--paper-secondary); margin-top:0.25rem;">
                Executive summary and candidate issue breakdown generated 100% locally on this computer.
            </div>
        </div>
        """
    )

    # 2. Main Two-Column Layout
    col_main, col_stats = st.columns([7, 5], gap="large")

    with col_main:
        # Summary Card
        summary_text = result.summary or "A plain-language summary could not be generated for this document."
        render_html(
            f"""
            <div class="rl-card">
                <div style="display:flex; align-items:center; justify-content:space-between; padding-bottom:0.75rem; border-bottom:1px solid var(--line); margin-bottom:0.75rem;">
                    <div style="display:flex; align-items:center; gap:0.5rem;">
                        <span class="rl-card-title" style="margin-bottom:0;">Document summary</span>
                        <span class="rl-badge rl-badge-neutral" style="font-size:11px;">Possible reading</span>
                    </div>
                    <span class="rl-mono" style="font-size:11px; color:var(--paper-muted);">{result.pages_analyzed} pages · {result.chunks_analyzed} sections</span>
                </div>
                <div style="font-family:'Fraunces', Georgia, serif; font-size:15px; line-height:1.6; color:var(--paper-primary); margin:0.75rem 0;">
                    {esc(summary_text)}
                </div>
                <div style="padding:0.6rem 0.75rem; border-radius:6px; background-color:var(--bg-inset); border:1px solid var(--line); font-size:12px; color:var(--paper-secondary); display:flex; align-items:center; gap:0.5rem;">
                    <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background-color:var(--ember); flex-shrink:0;"></span>
                    <span>Note: A quote found in the document confirms syntactic presence; it does not mean the reading is legally binding.</span>
                </div>
            </div>
            """
        )

        # Needs Professional Review Shortlist
        review_items = [f for f in findings if f.needs_human_review]
        render_html(
            f"""
            <div style="display:flex; align-items:center; justify-content:space-between; margin:1.25rem 0 0.5rem 0;">
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    {svg_icon("user_check", 18, "var(--review)")}
                    <span class="rl-card-title" style="font-size:17px; margin-bottom:0;">Needs professional review</span>
                    <span class="rl-badge rl-badge-review" style="font-size:11px; height:20px; padding:0 0.5rem;">{len(review_items)}</span>
                </div>
                <span style="font-size:12px; color:var(--paper-muted);">Prioritize these clauses</span>
            </div>
            """
        )

        if review_items:
            for idx, item in enumerate(review_items[:5]):
                col_r1, col_r2 = st.columns([5, 1])
                with col_r1:
                    render_html(
                        f"""
                        <div style="padding:0.65rem 0.85rem; margin:0.25rem 0; border-radius:8px; background:var(--bg-surface); border:1px solid var(--line); display:flex; align-items:center; gap:0.65rem;">
                            <span style="width:8px; height:8px; border-radius:50%; background-color:var(--review); flex-shrink:0;"></span>
                            <div>
                                <div style="font-weight:600; font-size:13.5px; color:var(--paper-primary);">{esc(item.title)}</div>
                                <div style="font-size:11.5px; color:var(--paper-muted);">{esc(item.category.capitalize())} · Page {item.page}</div>
                            </div>
                        </div>
                        """
                    )
                with col_r2:
                    if st.button("Open", key=f"ov_open_review_{idx}", use_container_width=True):
                        st.session_state["selected_finding"] = item.title
                        st.session_state["viewer_page"] = item.page
                        st.session_state["viewer_quote"] = item.evidence_quote
                        set_route("Findings")
                        st.rerun()
        else:
            render_html(
                """
                <div class="rl-card" style="padding:1rem; color:var(--paper-muted); font-size:13px; text-align:center;">
                    No clauses flagged for priority professional review.
                </div>
                """
            )

        # Prompt-Injection Notice
        injection_notice = any("Text resembling instructions to an AI" in limit for limit in result.limitations)
        if injection_notice:
            render_html(
                f"""
                <div class="rl-callout" style="margin:1rem 0;">
                    {svg_icon("info", 18, "var(--paper-muted)")}
                    <div>
                        <strong style="color:var(--paper-primary);">Notice:</strong> This document contains text resembling instructions to an AI.
                        It was treated strictly as document content and disregarded during triage prompt assembly.
                    </div>
                </div>
                """
            )

        # Limitations Expander - Open by default
        with st.expander("⚠️ System Limitations & Processing Notes", expanded=True):
            items_li = "".join(f"<li style='margin-bottom:0.25rem;'>{esc(item)}</li>" for item in result.limitations)
            render_html(
                f"""
                <ul style="font-size:13px; color:var(--paper-secondary); padding-left:1.25rem; line-height:1.5;">
                    {items_li}
                </ul>
                """
            )

        # Full Persistent Disclaimer with Escalation Guidance
        render_disclaimer(full=True)

    with col_stats:
        # Counts by category
        categories_map: dict[str, int] = {}
        for f in findings:
            cat_name = f.category.capitalize()
            categories_map[cat_name] = categories_map.get(cat_name, 0) + 1

        max_count = max(categories_map.values()) if categories_map else 1

        bars_html = []
        for cat_name, cnt in sorted(categories_map.items(), key=lambda x: x[1], reverse=True):
            pct = int((cnt / max_count) * 100)
            bars_html.append(
                f"""
                <div style="padding:0.4rem 0; border-bottom:1px solid var(--line);">
                    <div style="display:flex; align-items:center; justify-content:space-between; font-size:12.5px; margin-bottom:0.25rem;">
                        <span style="color:var(--paper-primary); font-weight:500;">{esc(cat_name)}</span>
                        <span class="rl-mono" style="font-size:11.5px; color:var(--paper-muted);">{cnt}</span>
                    </div>
                    <div style="width:100%; height:6px; border-radius:999px; background:var(--bg-inset); overflow:hidden;">
                        <div style="height:100%; width:{pct}%; border-radius:999px; background:var(--marker);"></div>
                    </div>
                </div>
                """
            )

        render_html(
            f"""
            <div class="rl-card">
                <div style="display:flex; align-items:center; justify-content:space-between; padding-bottom:0.5rem; margin-bottom:0.5rem; border-bottom:1px solid var(--line);">
                    <span class="rl-card-title" style="font-size:16px; margin-bottom:0;">Counts by category</span>
                    <span class="rl-mono" style="font-size:11px; color:var(--paper-muted);">{len(categories_map)} categories</span>
                </div>
                <div>
                    {''.join(bars_html)}
                </div>
            </div>
            """
        )

        # Quick Jump to Findings
        if st.button("🔎 Review all candidate findings", type="primary", use_container_width=True):
            set_route("Findings")
            st.rerun()
