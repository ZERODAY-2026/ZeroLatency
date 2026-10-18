"""Home landing page implementation (full-bleed, no rail).

Features:
- Headline with Fraunces serif and marker highlight
- Orbit of trust animated SVG illustration
- Stepper for "How Redline works" (native st.columns + border containers)
- 3-column card grid for "What you get" (native st.columns + border containers)
- Honest limits two-column comparison
- Fully semantic rl-* CSS classes and native Streamlit layout
"""

import streamlit as st
from src.config import settings

from .html import render_html, esc
from .icons import svg_icon
from .state import set_route
from .text import (
    APP_NAME,
    DISCLAIMER_FULL,
    HOME_CTA_PRIMARY,
    HOME_CTA_SECONDARY,
    HOME_HERO_HEADLINE_HIGHLIGHT,
    HOME_HERO_HEADLINE_POST,
    HOME_HERO_HEADLINE_PRE,
    HOME_HERO_SUBTEXT,
    HOME_HONEST_LIMITS_DOES,
    HOME_HONEST_LIMITS_NEVER,
    HOME_HOW_IT_WORKS,
    HOME_PRIVACY_CALLOUT,
    HOME_WHAT_YOU_GET,
    TESTED_ON_DOCUMENTS,
)


def render_home() -> None:
    """Render the full-bleed Home landing page."""
    # Top Masthead
    render_html(
        f"""
        <div style="display:flex; align-items:center; justify-content:space-between; padding-bottom:1.25rem; margin-bottom:1.5rem; border-bottom:1px solid var(--line);">
            <div style="display:flex; align-items:center; gap:0.75rem;">
                <div style="width:36px; height:36px; border-radius:8px; background:var(--bg-surface); border:1px solid var(--line); display:flex; align-items:center; justify-content:center; font-size:18px;">
                    ⚖️
                </div>
                <div>
                    <div class="rl-h1" style="font-size:20px; font-weight:600; line-height:1.1;">{esc(APP_NAME)}</div>
                    <div style="font-size:10px; color:var(--paper-muted); text-transform:uppercase; letter-spacing:0.06em; margin-top:2px;">Private legal triage · Zero telemetry</div>
                </div>
            </div>
            <div>
                <span class="rl-badge rl-badge-local">
                    <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background-color:var(--local-teal);" class="anim-breathing-dot"></span>
                    <span>Offline Local Processing</span>
                </span>
            </div>
        </div>
        """
    )

    # Hero Section: Two Columns (Headline + Orbit Animation)
    col_hero_left, col_hero_right = st.columns([7, 5], gap="large")

    with col_hero_left:
        render_html(
            f"""
            <div class="rl-hero">
                <div class="rl-chip" style="margin-bottom:1rem;">
                    <span class="rl-mono" style="font-size:11px; color:var(--paper-muted); text-transform:uppercase;">Engine:</span>
                    <span style="color:var(--paper-primary); font-weight:500;">{esc(settings.model)}</span>
                    <span style="padding:0.1rem 0.35rem; border-radius:4px; background:var(--bg-inset); color:var(--paper-muted); font-size:10px;">100% offline</span>
                </div>
                <h1 class="rl-hero-title">
                    {esc(HOME_HERO_HEADLINE_PRE)}
                    <span class="rl-hero-highlight">{esc(HOME_HERO_HEADLINE_HIGHLIGHT)}</span><br/>
                    {esc(HOME_HERO_HEADLINE_POST)}
                </h1>
                <p class="rl-hero-sub">
                    {esc(HOME_HERO_SUBTEXT)}
                </p>
                <div style="font-size:13px; color:var(--paper-muted); margin-bottom:1.5rem;">
                    {esc(HOME_PRIVACY_CALLOUT)}
                </div>
            </div>
            """
        )

        col_cta1, col_cta2 = st.columns([1, 1])
        with col_cta1:
            if st.button("🚀 Open my desk", type="primary", use_container_width=True, key="home_cta_desk"):
                set_route("Desk")
                st.rerun()

        with col_cta2:
            if st.button("🛡️ See how privacy works", use_container_width=True, key="home_cta_privacy"):
                set_route("Privacy and model")
                st.rerun()

    with col_hero_right:
        # A6 Orbit of Trust Mechanical SVG Animation
        render_html(
            """
            <div style="display:flex; align-items:center; justify-content:center; padding:1rem;">
                <svg width="280" height="280" viewBox="0 0 320 320" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="160" cy="160" r="120" stroke="#433E34" stroke-width="1.5" stroke-dasharray="4 6"/>
                    <path d="M 280 160 L 310 160" stroke="#FF7A8A" stroke-width="2" stroke-dasharray="3 3"/>
                    <circle cx="295" cy="160" r="4" fill="#FF7A8A"/>
                    <line x1="292" y1="157" x2="298" y2="163" stroke="#0D0C0A" stroke-width="1.5"/>

                    <circle cx="160" cy="160" r="36" fill="#181612" stroke="#2C2923" stroke-width="1.5"/>
                    <rect x="146" y="148" width="28" height="18" rx="2" stroke="#F7D748" stroke-width="1.8"/>
                    <line x1="142" y1="170" x2="178" y2="170" stroke="#F7D748" stroke-width="2" stroke-linecap="round"/>

                    <g class="anim-orbit" style="transform-origin: 160px 160px;">
                        <g transform="translate(160, 40)">
                            <circle cx="0" cy="0" r="18" fill="#181612" stroke="#F7D748" stroke-width="1.5"/>
                            <rect x="-6" y="-8" width="12" height="16" rx="1" stroke="#F3EDE0" stroke-width="1.2"/>
                        </g>
                        <g transform="translate(264, 220)">
                            <circle cx="0" cy="0" r="18" fill="#181612" stroke="#4FE3C8" stroke-width="1.5"/>
                            <circle cx="0" cy="0" r="6" stroke="#4FE3C8" stroke-width="1.5"/>
                        </g>
                        <g transform="translate(56, 220)">
                            <circle cx="0" cy="0" r="18" fill="#181612" stroke="#7CC4FF" stroke-width="1.5"/>
                            <path d="M-5 -2 L-1 3 L6 -5" stroke="#7CC4FF" stroke-width="1.5" stroke-linecap="round"/>
                        </g>
                    </g>
                </svg>
            </div>
            """
        )

    render_html('<div class="rl-divider"></div>')

    # How It Works Stepper (3-step horizontal)
    render_html(
        """
        <div style="margin-bottom:0.75rem;">
            <div class="rl-card-title" style="font-size:20px;">How Redline works</div>
        </div>
        """
    )
    col_s1, col_s2, col_s3 = st.columns(3)
    for col, step in zip([col_s1, col_s2, col_s3], HOME_HOW_IT_WORKS):
        with col:
            with st.container(border=True):
                render_html(
                    f"""
                    <div style="padding:0.25rem;">
                        <div class="rl-step-num">{esc(step['step'])}</div>
                        <div class="rl-step-title">{esc(step['title'])}</div>
                        <div class="rl-step-desc">{esc(step['desc'])}</div>
                    </div>
                    """
                )

    render_html('<div style="height: 1.5rem;"></div>')

    # What You Get Cards (3-column card grid)
    render_html(
        """
        <div style="margin-bottom:0.75rem;">
            <div class="rl-card-title" style="font-size:20px;">What you get</div>
        </div>
        """
    )
    col_w1, col_w2, col_w3 = st.columns(3)
    for col, card in zip([col_w1, col_w2, col_w3], HOME_WHAT_YOU_GET):
        with col:
            with st.container(border=True):
                render_html(
                    f"""
                    <div style="padding:0.25rem;">
                        <div class="rl-card-title" style="font-size:16px;">{esc(card['title'])}</div>
                        <div class="rl-card-desc" style="font-size:13px; color:var(--paper-secondary); line-height:1.5;">{esc(card['desc'])}</div>
                    </div>
                    """
                )

    render_html('<div style="height: 1.5rem;"></div>')

    # Honest Limits (Two Columns: What it does vs What it will never do)
    render_html(
        """
        <div style="margin-bottom:0.5rem;">
            <div class="rl-card-title" style="font-size:20px; margin-bottom:0.25rem;">Honest about limits</div>
            <p style="font-size:13px; color:var(--paper-muted); margin-bottom:0.75rem;">Not a lawyer. Calibrated for informational document triage only.</p>
        </div>
        """
    )

    col_l1, col_l2 = st.columns(2)
    with col_l1:
        with st.container(border=True):
            does_items = "".join(
                f'<div style="display:flex; align-items:center; gap:0.5rem; font-size:13px; color:var(--paper-secondary); padding:0.35rem 0; border-bottom:1px solid var(--line);">{svg_icon("check", 14, "var(--found)")} <span>{esc(item)}</span></div>'
                for item in HOME_HONEST_LIMITS_DOES
            )
            render_html(
                f"""
                <div style="padding:0.25rem;">
                    <div class="rl-card-title" style="font-size:16px;">What Redline does</div>
                    <div>{does_items}</div>
                </div>
                """
            )

    with col_l2:
        with st.container(border=True):
            never_items = "".join(
                f'<div style="display:flex; align-items:center; gap:0.5rem; font-size:13px; color:var(--paper-secondary); padding:0.35rem 0; border-bottom:1px solid var(--line);">{svg_icon("info", 14, "var(--paper-muted)")} <span>{esc(item)}</span></div>'
                for item in HOME_HONEST_LIMITS_NEVER
            )
            render_html(
                f"""
                <div style="padding:0.25rem;">
                    <div class="rl-card-title" style="font-size:16px;">What Redline will never do</div>
                    <div>{never_items}</div>
                </div>
                """
            )

    # Tested on strip & Footer
    tested_str = " · ".join(esc(item) for item in TESTED_ON_DOCUMENTS)
    render_html(
        f"""
        <div style="padding-top:2rem; margin-top:2rem; border-top:1px solid var(--line); text-align:center;">
            <div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:center; gap:0.75rem; font-size:12px; color:var(--paper-muted); margin-bottom:1rem;">
                <span style="font-weight:600;">Tested on:</span>
                <span>{tested_str}</span>
            </div>
            <div class="rl-callout" style="max-width:720px; margin:0 auto; text-align:left;">
                <div style="font-size:12px; color:var(--paper-muted); line-height:1.5;">
                    {esc(DISCLAIMER_FULL)}
                </div>
            </div>
            <div style="font-size:11px; color:var(--paper-muted); margin-top:1rem;">
                Gemma 3n · Apache 2.0 / Google Gemma License · Loopback execution only
            </div>
        </div>
        """
    )
