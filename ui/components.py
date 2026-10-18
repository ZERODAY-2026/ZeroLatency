"""Reusable UI components matching the approved design system.

Components:
- Empty state with CTAs ("Go to the Desk", "Use sample document", "Analyse document")
- Badges (explicit, interpretation, verified, unverified, confidence, review, jurisdiction, category)
- Finding card with quote block and verification breakdown
- Top bar and breadcrumbs
- Results header strip
- Persistent disclaimer
- Inline error card with next step and command copy
"""

from typing import Any
import streamlit as st

from .html import render_html, esc
from .icons import svg_icon
from .state import set_route
from .text import (
    DISCLAIMER_FULL,
    DISCLAIMER_SHORT,
    ESCALATION_ADVICE,
    ERROR_MAPPINGS,
)


def render_empty_state(page_title: str) -> None:
    """Render a clean empty state when an analysis result is not yet available."""
    has_doc = st.session_state.get("session") is not None

    render_html(
        f"""
        <div class="rl-empty-state anim-page-turn">
            <div class="rl-empty-icon">📄</div>
            <div class="rl-empty-title">{esc(page_title)}</div>
            <div class="rl-empty-desc">
                Analyse a document to see findings, quotes, key facts, and checklists here.
            </div>
        </div>
        """
    )

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if has_doc:
            if st.button("Analyse document", type="primary", key=f"empty_analyse_{page_title.lower().replace(' ', '_')}"):
                set_route("Desk")
                st.session_state["trigger_analysis"] = True
                st.rerun()
        else:
            if st.button("Go to the Desk", type="primary", key=f"empty_desk_{page_title.lower().replace(' ', '_')}"):
                set_route("Desk")
                st.rerun()

    with col2:
        if st.button("Use sample document", key=f"empty_sample_{page_title.lower().replace(' ', '_')}"):
            try:
                from .desk import load_sample_document
                load_sample_document()
                set_route("Desk")
                st.rerun()
            except Exception as ex:
                st.error(f"Could not load sample: {ex}")


def render_badge(badge_type: str, text: str, extra_class: str = "", tooltip: str = "") -> str:
    """Return HTML string for a styled pill badge using rl-badge classes."""
    title_attr = f' title="{esc(tooltip)}"' if tooltip else ""
    return f'<span class="rl-badge rl-badge-{esc(badge_type)} {esc(extra_class)}"{title_attr}>{text}</span>'


def render_finding_badges(finding: Any) -> str:
    """Build the badge cluster HTML for a finding card."""
    badges = []

    # Category chip
    cat = getattr(finding, "category", "general")
    badges.append(
        render_badge(
            "neutral",
            f'{svg_icon("tag", 13)} <span>{esc(cat.capitalize())}</span>',
        )
    )

    # Statement type: explicit vs interpretation
    st_type = getattr(finding, "statement_type", "explicit")
    if st_type == "explicit":
        badges.append(
            render_badge(
                "neutral",
                f'{svg_icon("description", 13)} <span>Stated in document</span>',
            )
        )
    else:
        badges.append(
            render_badge(
                "neutral",
                f'{svg_icon("help", 13)} <span>Possible reading</span>',
                extra_class="rl-badge-dashed",
            )
        )

    # Verification: verified vs unverified
    v_status = getattr(finding, "verification_status", "unverified")
    if v_status == "verified":
        badges.append(
            render_badge(
                "verified",
                f'{svg_icon("quote_check", 13, "var(--found)")} <span>Quote found in document</span>',
            )
        )
    else:
        badges.append(
            render_badge(
                "unverified",
                f'{svg_icon("triangle_alert", 13, "var(--ember)")} <span>Could not verify quote</span>',
            )
        )

    # Confidence: low, medium, high
    conf = getattr(finding, "confidence", "medium")
    conf_bars = {"low": "■□□", "medium": "■■□", "high": "■■■"}.get(conf, "■■□")
    badges.append(
        render_badge(
            "neutral",
            f'<span class="rl-mono" style="font-size:11px;">{conf_bars}</span> <span>Confidence: {esc(conf)}</span>',
            tooltip="Derived from checks, not from the model",
        )
    )

    # Review with professional
    if getattr(finding, "needs_human_review", False):
        badges.append(
            render_badge(
                "review",
                f'{svg_icon("user_check", 13, "var(--review)")} <span>Review with a professional</span>',
            )
        )

    # Jurisdiction dependent
    if getattr(finding, "jurisdiction_dependent", False):
        badges.append(
            render_badge(
                "jurisdiction",
                f'{svg_icon("globe", 13, "var(--jurisdiction)")} <span>Depends on local law</span>',
            )
        )

    return f'<div style="display:flex; flex-wrap:wrap; align-items:center; gap:0.4rem; margin:0.6rem 0;">{"".join(badges)}</div>'


def render_topbar(
    breadcrumb_page: str,
    doc_name: str | None = None,
    page_count: int | None = None,
) -> None:
    """Render the standard top bar with breadcrumb, document chip, and short disclaimer."""
    doc_chip_html = ""
    if doc_name:
        page_badge = f'<span class="rl-mono" style="font-size:11px; padding:0.15rem 0.4rem; background:var(--line); border-radius:4px; color:var(--paper-muted);">{page_count}p</span>' if page_count else ""
        doc_chip_html = f"""
        <div class="rl-chip">
            {svg_icon("description", 14, "var(--paper-secondary)")}
            <span class="rl-mono" style="font-size:12px; color:var(--paper-primary);">{esc(doc_name)}</span>
            {page_badge}
        </div>
        """

    render_html(
        f"""
        <div style="display:flex; align-items:center; justify-content:space-between; height:48px; border-bottom:1px solid var(--line); margin-bottom:1.5rem;">
            <div style="display:flex; align-items:center; gap:0.75rem;">
                <div style="display:flex; align-items:center; gap:0.4rem; font-size:13px; color:var(--paper-muted);">
                    <span>Desk</span>
                    <span style="color:var(--line-strong);">/</span>
                    <strong style="color:var(--paper-primary);">{esc(breadcrumb_page)}</strong>
                </div>
                {doc_chip_html}
            </div>
            <div style="display:flex; align-items:center; gap:0.5rem; font-size:12px; color:var(--paper-muted);">
                <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background-color:var(--ember);"></span>
                <span>{esc(DISCLAIMER_SHORT)}</span>
            </div>
        </div>
        """
    )


def render_results_header(
    doc_name: str,
    findings_count: int,
    verified_count: int,
    review_count: int,
    elapsed_seconds: float,
) -> None:
    """Render the 4-tile header strip shown on all analysis results pages."""
    mins = int(elapsed_seconds // 60)
    secs = int(elapsed_seconds % 60)
    elapsed_str = f"{mins:02d}:{secs:02d}"

    render_html(
        f"""
        <div class="rl-grid-4 anim-page-turn">
            <div class="rl-stat">
                <span class="rl-stat-label">Candidate Findings</span>
                <span class="rl-stat-val" style="color:var(--marker);">{findings_count}</span>
            </div>
            <div class="rl-stat">
                <span class="rl-stat-label">Quotes Found</span>
                <span class="rl-stat-val" style="color:var(--found);">{verified_count}</span>
            </div>
            <div class="rl-stat">
                <span class="rl-stat-label">Needs Review</span>
                <span class="rl-stat-val" style="color:var(--review);">{review_count}</span>
            </div>
            <div class="rl-stat">
                <span class="rl-stat-label">Elapsed Time</span>
                <span class="rl-stat-val rl-mono" style="font-size:24px;">{elapsed_str}</span>
            </div>
        </div>
        """
    )


def render_disclaimer(full: bool = False) -> None:
    """Render the persistent neutral disclaimer box."""
    text = DISCLAIMER_FULL if full else DISCLAIMER_SHORT
    render_html(
        f"""
        <div class="rl-callout">
            <span style="flex-shrink:0; margin-top:2px;">{svg_icon("scales", 16, "var(--paper-muted)")}</span>
            <div style="display:flex; flex-direction:column; gap:0.25rem; font-size:13px;">
                <span>{esc(text)}</span>
                {f'<span style="color:var(--paper-muted); font-size:12px;">{esc(ESCALATION_ADVICE)}</span>' if full else ''}
            </div>
        </div>
        """
    )


def render_error_card(error_name: str, message: str | None = None, next_step: str | None = None, command: str | None = None) -> None:
    """Render an inline error card mapped from the error table."""
    mapping = ERROR_MAPPINGS.get(error_name)
    title = mapping.title if mapping else "An error occurred during triage."
    desc = message or (mapping.message if mapping else "Please check your document and local configuration.")
    action = next_step or (mapping.next_step if mapping else "Try again.")
    cmd = command or (mapping.command if mapping else None)

    cmd_html = ""
    if cmd:
        cmd_html = f"""
        <div style="display:flex; align-items:center; justify-content:space-between; padding:0.6rem 0.75rem; margin:0.5rem 0; border-radius:6px; background-color:var(--bg-inset); border:1px solid var(--line); font-family:var(--font-mono); font-size:12px; color:var(--paper-primary);">
            <code>{esc(cmd)}</code>
            <span style="color:var(--paper-muted); font-size:11px;">Copyable command</span>
        </div>
        """

    render_html(
        f"""
        <div class="rl-card anim-page-turn" style="background-color:var(--error-red-bg); border-color:var(--error-red-border);">
            <div style="display:flex; align-items:center; gap:0.5rem; color:var(--error-red); font-weight:600; font-size:15px; margin-bottom:0.4rem;">
                {svg_icon("octagon_alert", 18, "var(--error-red)")}
                <span>{esc(title)}</span>
            </div>
            <div style="font-size:13px; color:var(--paper-secondary); line-height:1.5;">
                {esc(desc)}
            </div>
            {cmd_html}
            <div style="font-size:12px; color:var(--paper-muted); margin-top:0.4rem;">
                <strong style="color:var(--paper-secondary);">What to do:</strong> {esc(action)}
            </div>
        </div>
        """
    )
