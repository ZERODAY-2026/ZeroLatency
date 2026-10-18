"""Findings page implementation.

Features:
- Filter deck: Category, Type, Verification, Confidence, Needs Review toggle, Search query, Sort
- Two distinct groups: 'Quote found in document' and 'Could not be verified' (collapsed)
- Margin note finding cards with badges, verbatim quote blocks, and verification breakdowns
- Sticky side-by-side source viewer with highlighted source page
- Safe HTML rendering with semantic rl-* classes
"""

from typing import Any
import streamlit as st

from .components import (
    render_empty_state,
    render_finding_badges,
    render_results_header,
    render_topbar,
)
from .html import render_html, esc
from .source_view import render_source_viewer
from .text import (
    EMPTY_FILTER_TEXT,
    EMPTY_FINDINGS_TEXT,
    FINDINGS_SUBTITLE,
    FINDINGS_TITLE,
    GROUP_UNVERIFIED_EXPLANATION,
    GROUP_UNVERIFIED_TITLE,
    GROUP_VERIFIED_TITLE,
    HOW_CHECKED_LABEL,
    UNVERIFIED_QUOTE_LABEL,
    VERIFIED_QUOTE_LABEL,
    VIEW_IN_DOCUMENT_LABEL,
    VIEW_WITHOUT_HIGHLIGHT_LABEL,
)


def render_findings() -> None:
    """Render the candidate findings workspace."""
    result = st.session_state.get("result")
    session = st.session_state.get("session")
    doc_path = st.session_state.get("path")
    doc_name = st.session_state.get("doc_name", "document")

    render_topbar("Findings", doc_name=doc_name, page_count=len(session.pages) if session else None)

    if result is None or session is None or doc_path is None:
        render_empty_state("Findings")
        return

    findings = result.findings
    total_pages = len(session.pages)

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

    # 2. Page Title
    render_html(
        f"""
        <div style="margin-bottom:1.5rem;">
            <div class="rl-h1" style="font-size:28px; font-weight:600; color:var(--paper-primary);">{esc(FINDINGS_TITLE)}</div>
            <div style="font-size:13px; color:var(--paper-secondary); margin-top:0.25rem;">{esc(FINDINGS_SUBTITLE)}</div>
        </div>
        """
    )

    # 3. Comprehensive Filter Bar
    with st.container():
        col_s, col_f1, col_f2, col_f3, col_f4, col_f5, col_sort = st.columns([3, 2, 2, 2, 2, 2, 2])

        with col_s:
            search_query = st.text_input(
                "Search",
                placeholder="Search claims or quotes...",
                value=st.session_state.get("search_query", ""),
                label_visibility="collapsed",
                key="find_search_input",
            )
            st.session_state["search_query"] = search_query

        categories = ["All"] + sorted(list({f.category.capitalize() for f in findings}))
        with col_f1:
            cat_choice = st.selectbox(
                "Category",
                options=categories,
                index=categories.index(st.session_state.get("selected_category", "All")) if st.session_state.get("selected_category") in categories else 0,
                label_visibility="collapsed",
                key="find_cat_select",
            )
            st.session_state["selected_category"] = cat_choice

        type_options = ["All", "Stated in document", "Possible reading"]
        with col_f2:
            type_choice = st.selectbox(
                "Statement Type",
                options=type_options,
                index=type_options.index(st.session_state.get("selected_type", "All")),
                label_visibility="collapsed",
                key="find_type_select",
            )
            st.session_state["selected_type"] = type_choice

        verif_options = ["All", "Verified quotes only", "Unverified"]
        with col_f3:
            verif_choice = st.selectbox(
                "Verification",
                options=verif_options,
                index=verif_options.index(st.session_state.get("selected_verification", "All")),
                label_visibility="collapsed",
                key="find_verif_select",
            )
            st.session_state["selected_verification"] = verif_choice

        conf_options = ["All", "High", "Medium", "Low"]
        with col_f4:
            conf_choice = st.selectbox(
                "Confidence",
                options=conf_options,
                index=conf_options.index(st.session_state.get("selected_confidence", "All")),
                label_visibility="collapsed",
                key="find_conf_select",
            )
            st.session_state["selected_confidence"] = conf_choice

        with col_f5:
            needs_review_filter = st.checkbox(
                "Needs review only",
                value=st.session_state.get("filter_needs_review", False),
                key="find_review_chk",
            )
            st.session_state["filter_needs_review"] = needs_review_filter

        sort_options = ["Page order", "Confidence (high)", "Needs review priority"]
        with col_sort:
            sort_choice = st.selectbox(
                "Sort",
                options=sort_options,
                index=sort_options.index(st.session_state.get("sort_order", "Page order")),
                label_visibility="collapsed",
                key="find_sort_select",
            )
            st.session_state["sort_order"] = sort_choice

    # 4. Filter and Sort Logic
    filtered: list[Any] = []
    for f in findings:
        if search_query:
            sq = search_query.lower()
            if sq not in f.title.lower() and sq not in f.explanation.lower() and sq not in f.evidence_quote.lower():
                continue

        if cat_choice != "All" and f.category.lower() != cat_choice.lower():
            continue

        if type_choice == "Stated in document" and f.statement_type != "explicit":
            continue
        if type_choice == "Possible reading" and f.statement_type != "interpretation":
            continue

        if verif_choice == "Verified quotes only" and f.verification_status != "verified":
            continue
        if verif_choice == "Unverified" and f.verification_status != "unverified":
            continue

        if conf_choice != "All" and f.confidence.lower() != conf_choice.lower():
            continue

        if needs_review_filter and not f.needs_human_review:
            continue

        filtered.append(f)

    # Sorting
    if sort_choice == "Page order":
        filtered.sort(key=lambda x: x.page)
    elif sort_choice == "Confidence (high)":
        order_map = {"high": 3, "medium": 2, "low": 1}
        filtered.sort(key=lambda x: order_map.get(x.confidence, 0), reverse=True)
    elif sort_choice == "Needs review priority":
        filtered.sort(key=lambda x: (not x.needs_human_review, x.page))

    # 5. Two-Column Layout (List on Left, Sticky Source Viewer on Right)
    col_cards, col_viewer = st.columns([7, 5], gap="large")

    with col_cards:
        if not findings:
            render_html(f'<div class="rl-card" style="text-align:center; padding:2rem; color:var(--paper-muted);">{esc(EMPTY_FINDINGS_TEXT)}</div>')
        elif not filtered:
            render_html(
                f"""
                <div class="rl-card" style="text-align:center; padding:2rem; color:var(--paper-muted);">
                    <p style="font-size:15px; margin-bottom:1rem;">{esc(EMPTY_FILTER_TEXT)}</p>
                </div>
                """
            )
            if st.button("Reset filters", key="reset_filters_btn"):
                st.session_state["search_query"] = ""
                st.session_state["selected_category"] = "All"
                st.session_state["selected_type"] = "All"
                st.session_state["selected_verification"] = "All"
                st.session_state["selected_confidence"] = "All"
                st.session_state["filter_needs_review"] = False
                st.rerun()
        else:
            verified_list = [f for f in filtered if f.verification_status == "verified"]
            unverified_list = [f for f in filtered if f.verification_status != "verified"]

            # Group 1: Quote Found in Document
            render_html(
                f"""
                <div style="display:flex; align-items:center; gap:0.5rem; margin:0.5rem 0 0.75rem 0;">
                    <span class="rl-card-title" style="font-size:18px; margin-bottom:0;">{esc(GROUP_VERIFIED_TITLE)}</span>
                    <span class="rl-badge rl-badge-verified" style="font-size:11px; height:20px; padding:0 0.5rem;">{len(verified_list)}</span>
                </div>
                """
            )

            for idx, finding in enumerate(verified_list):
                _render_finding_card(finding, idx, is_verified=True)

            # Group 2: Could not be verified (Collapsed by default)
            if unverified_list:
                render_html('<div class="rl-divider"></div>')
                with st.expander(f"⚠️ {GROUP_UNVERIFIED_TITLE} ({len(unverified_list)})", expanded=False):
                    render_html(
                        f"""
                        <div class="rl-callout" style="background-color:var(--ember-bg); border-color:var(--ember-border); color:var(--ember);">
                            {esc(GROUP_UNVERIFIED_EXPLANATION)}
                        </div>
                        """
                    )
                    for idx, finding in enumerate(unverified_list):
                        _render_finding_card(finding, idx + 1000, is_verified=False)

    with col_viewer:
        render_source_viewer(
            doc_path=doc_path,
            total_pages=total_pages,
            current_page=st.session_state.get("viewer_page", 1),
            highlight_quote=st.session_state.get("viewer_quote"),
            pages_data=session.pages,
        )


def _render_finding_card(finding: Any, card_idx: int, is_verified: bool) -> None:
    """Render a single margin-note finding card with buttons and expanders."""
    selected_finding = st.session_state.get("selected_finding")
    is_selected = selected_finding == finding.title
    card_cls = "rl-card rl-card-selected" if is_selected else "rl-card"

    badges_html = render_finding_badges(finding)
    quote_label = VERIFIED_QUOTE_LABEL if is_verified else UNVERIFIED_QUOTE_LABEL
    quote_cls = "rl-quote" if is_verified else "rl-quote rl-quote-unverified"

    render_html(
        f"""
        <div class="{card_cls}">
            <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:0.75rem;">
                <div class="rl-card-title" style="font-size:16px; margin-bottom:0.25rem;">{esc(finding.title)}</div>
                <span class="rl-mono" style="font-size:11px; padding:0.15rem 0.45rem; border-radius:4px; background:var(--bg-inset); border:1px solid var(--line); color:var(--paper-muted); flex-shrink:0;">
                    p. {finding.page}
                </span>
            </div>
            {badges_html}
            <div class="rl-card-body" style="margin:0.5rem 0;">
                {esc(finding.explanation)}
            </div>
            <div class="{quote_cls}">
                <div style="font-size:10px; color:var(--paper-muted); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.25rem;">{esc(quote_label)}</div>
                <div>"{esc(finding.evidence_quote)}"</div>
            </div>
        </div>
        """
    )

    # Action Buttons: View in document & How checked
    col_act1, col_act2 = st.columns([1, 1])
    with col_act1:
        btn_label = f"📖 {VIEW_IN_DOCUMENT_LABEL}" if is_verified else f"📄 {VIEW_WITHOUT_HIGHLIGHT_LABEL}"
        if st.button(btn_label, key=f"view_finding_{card_idx}", use_container_width=True):
            st.session_state["selected_finding"] = finding.title
            st.session_state["viewer_page"] = finding.page
            st.session_state["viewer_quote"] = finding.evidence_quote if is_verified else None
            st.rerun()

    with col_act2:
        with st.expander(f"🔍 {HOW_CHECKED_LABEL}"):
            render_html(
                f"""
                <div class="rl-mono" style="font-size:12px; color:var(--paper-secondary); line-height:1.6; padding:0.25rem;">
                    <div><strong>Verification Note:</strong> {esc(finding.verification_note)}</div>
                    <div><strong>Location:</strong> Page {finding.page} (section: {esc(finding.chunk_id)})</div>
                </div>
                """
            )
            if finding.ungrounded_figures:
                render_html(
                    f"""
                    <div style="padding:0.5rem; margin-top:0.5rem; border-radius:6px; background-color:var(--ember-bg); border:1px solid var(--ember-border); font-size:12px; color:var(--ember);">
                        <strong>Ungrounded Figures:</strong> These figures do not appear in the document: {', '.join(esc(str(x)) for x in finding.ungrounded_figures)}
                    </div>
                    """
                )
