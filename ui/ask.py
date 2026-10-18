"""Ask the document Q&A page implementation.

Features:
- Large search input with marker caret and example question chips
- Four distinct answer states:
  1. Answered: Cited answer text, badges, verbatim evidence blocks, page jumps
  2. Silent: Neutral informative card ('The document doesn't seem to address this.')
  3. Verdict declined: Violet accent banner ('I can't say whether this is legal or enforceable')
  4. Unverified evidence: Warning border
- Preserves answer history for the session (stacked newest first)
- Safe HTML rendering with semantic rl-* classes
"""

import streamlit as st

from src.pipeline import DocumentSession
from src.privacy import network_guard
from src.schemas import Answer

from .components import render_empty_state, render_topbar
from .html import render_html, esc
from .icons import svg_icon
from .text import (
    ANSWER_EMPTY_INPUT_MSG,
    ANSWER_SILENT_MESSAGE,
    ANSWER_SILENT_TITLE,
    ANSWER_VERDICT_MESSAGE,
    ANSWER_VERDICT_TITLE,
    ASK_BUTTON_LABEL,
    ASK_INPUT_PLACEHOLDER,
    ASK_TITLE,
    DISCLAIMER_SHORT,
    ESCALATION_ADVICE,
)


def render_ask() -> None:
    """Render the Ask the document workspace."""
    session: DocumentSession | None = st.session_state.get("session")
    doc_name = st.session_state.get("doc_name", "document")

    render_topbar("Ask", doc_name=doc_name, page_count=len(session.pages) if session else None)

    if session is None:
        render_empty_state("Ask the document")
        return

    render_html(
        f"""
        <div style="margin-bottom:1.5rem;">
            <div class="rl-h1" style="font-size:28px; font-weight:600; color:var(--paper-primary);">{esc(ASK_TITLE)}</div>
            <div style="font-size:13px; color:var(--paper-secondary); margin-top:0.25rem;">
                Ask specific questions about clauses, fees, or obligations. All answers are grounded in cited passages.
            </div>
        </div>
        """
    )

    # Question Input & Primary Ask Action
    col_in, col_btn = st.columns([5, 1])
    with col_in:
        question = st.text_input(
            "Question",
            placeholder=ASK_INPUT_PLACEHOLDER,
            label_visibility="collapsed",
            key="ask_question_input",
        )
    with col_btn:
        ask_clicked = st.button(f"🔍 {ASK_BUTTON_LABEL}", type="primary", use_container_width=True)

    # Example chip buttons
    col_ex1, col_ex2, col_ex3 = st.columns(3)
    with col_ex1:
        if st.button("⏱️ When can it be terminated?", key="chip_term", use_container_width=True):
            _ask_and_store(session, "When can either party terminate this agreement?")
    with col_ex2:
        if st.button("💰 What fees or penalties apply?", key="chip_fees", use_container_width=True):
            _ask_and_store(session, "What fees or financial penalties are specified?")
    with col_ex3:
        if st.button("📅 What notice period is required?", key="chip_notice", use_container_width=True):
            _ask_and_store(session, "What notice period is required before termination?")

    # Handle typed submission
    if ask_clicked:
        if not question.strip():
            st.info(ANSWER_EMPTY_INPUT_MSG)
        else:
            _ask_and_store(session, question.strip())

    # Stacked Answer Cards (Newest First)
    answers: list[Answer] = st.session_state.get("answers", [])
    if answers:
        render_html('<div class="rl-divider"></div>')
        render_html(
            f"""
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem;">
                <span class="rl-card-title" style="font-size:18px; margin-bottom:0;">Session questions ({len(answers)})</span>
                <span style="font-size:12px; color:var(--paper-muted);">{esc(DISCLAIMER_SHORT)}</span>
            </div>
            """
        )

        for idx, ans in enumerate(reversed(answers)):
            _render_answer_card(ans, idx)


def _ask_and_store(session: DocumentSession, question: str) -> None:
    """Execute session.ask inside network_guard and prepend to answers list."""
    with st.spinner("Reading the document locally..."):
        observed: list[str] = []
        try:
            with network_guard(observed):
                answer_obj = session.ask(question)
                st.session_state.setdefault("answers", []).append(answer_obj)
                st.rerun()
        except Exception as exc:
            st.error(f"Could not complete local query: {exc}")


def _render_answer_card(ans: Answer, card_idx: int) -> None:
    """Render an individual answer card according to its state."""
    # State 1: Verdict Declined
    if getattr(ans, "verdict_declined", False):
        render_html(
            f"""
            <div class="rl-card anim-page-turn" style="border-color:var(--review-border); background-color:var(--review-bg);">
                <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.5rem; color:var(--review); font-weight:600; font-size:15px;">
                    {svg_icon("scales", 18, "var(--review)")}
                    <span>{esc(ANSWER_VERDICT_TITLE)}</span>
                </div>
                <div style="font-weight:600; color:var(--paper-primary); font-size:15px; margin-bottom:0.5rem; font-family:'Fraunces', serif;">
                    Q: {esc(ans.question)}
                </div>
                <div style="font-size:13px; color:var(--paper-muted); margin-bottom:0.5rem;">{esc(ANSWER_VERDICT_MESSAGE)}</div>
                <div style="font-size:14px; color:var(--paper-secondary); line-height:1.6; background-color:var(--bg-surface); padding:0.75rem; border-radius:6px; border:1px solid var(--line);">
                    {esc(ans.answer)}
                </div>
                <div style="font-size:12px; color:var(--paper-muted); margin-top:0.5rem;">
                    {esc(ans.escalation or ESCALATION_ADVICE)}
                </div>
            </div>
            """
        )
        return

    # State 2: Silent (Document does not address this) - Neutral style, not error!
    if not ans.answerable:
        render_html(
            f"""
            <div class="rl-card anim-page-turn">
                <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.4rem; color:var(--paper-secondary); font-weight:500; font-size:15px;">
                    {svg_icon("info", 18, "var(--paper-muted)")}
                    <span>{esc(ANSWER_SILENT_TITLE)}</span>
                </div>
                <div style="font-weight:600; color:var(--paper-primary); font-size:15px; margin-bottom:0.5rem; font-family:'Fraunces', serif;">
                    Q: {esc(ans.question)}
                </div>
                <p style="font-size:14px; color:var(--paper-secondary); line-height:1.6; margin-bottom:0.75rem;">
                    {esc(ans.answer or ANSWER_SILENT_MESSAGE)}
                </p>
                <div style="padding:0.6rem 0.75rem; border-radius:6px; background-color:var(--bg-inset); border:1px solid var(--line); font-size:12px; color:var(--paper-muted);">
                    {esc(ans.escalation or ESCALATION_ADVICE)}
                </div>
            </div>
            """
        )
        return

    # State 3 & 4: Answered (with verified or unverified evidence)
    st_type_badge = (
        '<span class="rl-badge rl-badge-neutral" style="font-size:11px;">Stated in document</span>'
        if ans.statement_type == "explicit"
        else '<span class="rl-badge rl-badge-neutral" style="font-size:11px; border-style:dashed;">Possible reading</span>'
    )

    evidence_blocks = []
    for e_idx, ev in enumerate(ans.evidence):
        is_verif = ev.verification_status == "verified"
        quote_style = "rl-quote" if is_verif else "rl-quote rl-quote-unverified"
        verif_note = (
            '<span class="rl-mono" style="color:var(--found); font-size:10px;">Quote verified</span>'
            if is_verif
            else '<span class="rl-mono" style="color:var(--ember); font-size:10px;">⚠️ Unverified quote</span>'
        )
        page_chip = f'<span class="rl-mono" style="font-size:11px; color:var(--paper-muted);">p. {ev.page}</span>' if ev.page else ""

        evidence_blocks.append(
            f"""
            <div class="{quote_style}">
                <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:0.25rem;">
                    {verif_note}
                    {page_chip}
                </div>
                <div>"{esc(ev.quote)}"</div>
            </div>
            """
        )

    render_html(
        f"""
        <div class="rl-card anim-page-turn">
            <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:0.75rem; margin-bottom:0.5rem;">
                <h3 class="rl-card-title" style="font-size:16px; margin-bottom:0;">Q: {esc(ans.question)}</h3>
                {st_type_badge}
            </div>
            <div style="font-size:14px; color:var(--paper-secondary); line-height:1.6; margin:0.5rem 0;">
                {esc(ans.answer)}
            </div>
            <div style="margin-top:0.75rem;">
                <div style="font-size:11px; color:var(--paper-muted); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.25rem;">Cited Evidence</div>
                {''.join(evidence_blocks)}
            </div>
            {f'<div style="margin-top:0.5rem; font-size:12px; color:var(--review);">{esc(ans.escalation)}</div>' if ans.jurisdiction_dependent else ''}
        </div>
        """
    )
