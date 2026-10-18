"""Privacy and model verification page.

Features:
- Giant hero statement: 'What leaves this device during processing: NOTHING.'
- Live device status card with aligned key-value metrics and breathing indicator
- Real <table> Network calls: Setup vs Processing
- Verification steps with loopback monitor commands
- Honest threat model and benchmark metrics (no internal labels or unverified claims)
"""

import streamlit as st
from src.config import settings

from .components import render_topbar
from .html import render_html, esc
from .icons import svg_icon
from .text import (
    PRIVACY_HERO_STATEMENT,
    PRIVACY_MONITOR_CMD_UNIX,
    PRIVACY_MONITOR_CMD_WIN,
    PRIVACY_STATUS_TITLE,
    PRIVACY_VERIFY_STEPS,
    PRIVACY_VERIFY_TITLE,
)


def render_privacy_page() -> None:
    """Render the privacy and model verification view."""
    doc_name = st.session_state.get("doc_name")
    session = st.session_state.get("session")
    page_count = len(session.pages) if session and session.pages else None

    # Top Bar
    render_topbar("Privacy and model", doc_name, page_count)

    # Giant Privacy Hero Statement
    render_html(
        f"""
        <div class="rl-card anim-page-turn" style="background-color:var(--bg-inset); border-color:var(--local-teal-border); padding:1.5rem 1.75rem; margin-bottom:1.5rem;">
            <div class="rl-eyebrow" style="color:var(--local-teal); margin-bottom:0.4rem;">Privacy Architecture</div>
            <div style="font-family:'Fraunces', Georgia, serif; font-size:24px; font-weight:600; color:var(--paper-primary); letter-spacing:-0.01em;">
                {esc(PRIVACY_HERO_STATEMENT)}
            </div>
            <div style="font-size:13px; color:var(--paper-secondary); margin-top:0.4rem; max-width:760px; line-height:1.5;">
                Every token is generated locally by a weights file residing on your local storage drive.
                No network socket connections outside loopback (127.0.0.1) are opened during analysis.
            </div>
        </div>
        """
    )

    col_live, col_verify = st.columns(2, gap="large")

    with col_live:
        # 1. Live Device Status Card
        blocked_hosts: list[str] = st.session_state.get("blocked_hosts", [])
        is_blocked = len(blocked_hosts) > 0

        status_badge = (
            f'<span class="rl-badge rl-badge-unverified">⚠️ {len(blocked_hosts)} Blocked</span>'
            if is_blocked
            else '<span class="rl-badge rl-badge-local"><span style="display:inline-block; width:6px; height:6px; border-radius:50%; background-color:var(--local-teal);" class="anim-breathing-dot"></span> Active · 0 Violations</span>'
        )

        render_html(
            f"""
            <div class="rl-card">
                <div style="display:flex; align-items:center; justify-content:space-between; padding-bottom:0.75rem; border-bottom:1px solid var(--line); margin-bottom:0.5rem;">
                    <span class="rl-card-title" style="margin-bottom:0;">{esc(PRIVACY_STATUS_TITLE)}</span>
                    {status_badge}
                </div>
                <div class="rl-kv-row">
                    <span class="rl-kv-label">Processing Endpoint</span>
                    <span class="rl-kv-val rl-mono">{esc(settings.ollama_url)}</span>
                </div>
                <div class="rl-kv-row">
                    <span class="rl-kv-label">Network Guard</span>
                    <span class="rl-kv-val" style="color:var(--local-teal);">
                        <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background-color:var(--local-teal);" class="anim-breathing-dot"></span>
                        Active · Strict Loopback Enforced
                    </span>
                </div>
                <div class="rl-kv-row">
                    <span class="rl-kv-label">Blocked Connection Attempts</span>
                    <span class="rl-kv-val rl-mono">{len(blocked_hosts)} this session</span>
                </div>
                <div class="rl-kv-row">
                    <span class="rl-kv-label">Storage Persistence</span>
                    <span class="rl-kv-val" style="font-size:12px;">Temporary private folder (deleted on exit)</span>
                </div>
            </div>
            """
        )

        # 2. Real Table: Network Calls (Setup vs Processing)
        render_html(
            """
            <div class="rl-card">
                <span class="rl-card-title">Network calls: Setup vs Processing</span>
                <div class="rl-table-container">
                    <table class="rl-table">
                        <thead>
                            <tr>
                                <th>Phase</th>
                                <th>Destination</th>
                                <th>Document Exposure</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Model Install</td>
                                <td class="rl-mono">ollama.com</td>
                                <td>None (weights only)</td>
                            </tr>
                            <tr style="background-color:var(--bg-raised); font-weight:500;">
                                <td style="color:var(--paper-primary);">Triage Processing</td>
                                <td class="rl-mono" style="color:var(--local-teal);">127.0.0.1:11434</td>
                                <td style="color:var(--local-teal);">0 bytes leave machine</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            """
        )

    with col_verify:
        # 3. How to Verify Steps
        steps_html = []
        for step in PRIVACY_VERIFY_STEPS:
            steps_html.append(
                f"""
                <div style="display:flex; align-items:flex-start; gap:0.75rem; padding:0.6rem 0; border-bottom:1px solid var(--line);">
                    <div style="width:24px; height:24px; border-radius:50%; background:var(--bg-inset); border:1px solid var(--line); display:flex; align-items:center; justify-content:center; font-family:var(--font-mono); font-size:11px; color:var(--paper-primary); flex-shrink:0;">
                        {esc(step['step'])}
                    </div>
                    <div>
                        <div style="font-weight:600; font-size:13px; color:var(--paper-primary);">{esc(step['title'])}</div>
                        <div style="font-size:12px; color:var(--paper-muted); margin-top:2px;">{esc(step['desc'])}</div>
                    </div>
                </div>
                """
            )

        render_html(
            f"""
            <div class="rl-card">
                <span class="rl-card-title">{esc(PRIVACY_VERIFY_TITLE)}</span>
                <div style="margin-bottom:0.75rem;">
                    {''.join(steps_html)}
                </div>
                <div style="font-size:11px; color:var(--paper-muted); margin-bottom:0.25rem; font-weight:600;">Loopback monitoring command (Windows):</div>
                <div style="padding:0.45rem 0.65rem; background:var(--bg-inset); border-radius:6px; border:1px solid var(--line); margin-bottom:0.6rem;">
                    <code class="rl-mono" style="font-size:11.5px; color:var(--paper-primary);">{esc(PRIVACY_MONITOR_CMD_WIN)}</code>
                </div>
                <div style="font-size:11px; color:var(--paper-muted); margin-bottom:0.25rem; font-weight:600;">Loopback monitoring command (macOS / Linux):</div>
                <div style="padding:0.45rem 0.65rem; background:var(--bg-inset); border-radius:6px; border:1px solid var(--line);">
                    <code class="rl-mono" style="font-size:11.5px; color:var(--paper-primary);">{esc(PRIVACY_MONITOR_CMD_UNIX)}</code>
                </div>
            </div>
            """
        )

    # Threat Model & Benchmark Metrics
    col_threat, col_bench = st.columns(2, gap="large")

    with col_threat:
        render_html(
            """
            <div class="rl-card">
                <span class="rl-card-title">Threat model & boundaries</span>
                <div class="rl-card-body" style="display:flex; flex-direction:column; gap:0.5rem;">
                    <div>
                        <strong style="color:var(--paper-primary);">In Scope:</strong>
                        Zero document transmission over the network; loopback-only processing; temporary private workspace folder deleted on cleanup.
                    </div>
                    <div>
                        <strong style="color:var(--paper-primary);">Out of Scope:</strong>
                        Malware residing on the host operating system with kernel-level inspection privileges; physical storage drive forensic analysis before data overwrite.
                    </div>
                </div>
            </div>
            """
        )

    with col_bench:
        result = st.session_state.get("result")
        pages_count = result.pages_analyzed if result else (page_count if page_count else 0)
        chunks_count = result.chunks_analyzed if result else 0
        elapsed_s = result.elapsed_seconds if result else 0.0

        render_html(
            f"""
            <div class="rl-card">
                <span class="rl-card-title">Benchmark metrics</span>
                <div class="rl-grid-2" style="margin-bottom:0.5rem;">
                    <div class="rl-stat" style="padding:0.5rem 0.75rem;">
                        <span class="rl-stat-label">Pages Analysed</span>
                        <span class="rl-stat-val" style="font-size:22px;">{pages_count}</span>
                    </div>
                    <div class="rl-stat" style="padding:0.5rem 0.75rem;">
                        <span class="rl-stat-label">Chunks Analysed</span>
                        <span class="rl-stat-val" style="font-size:22px;">{chunks_count}</span>
                    </div>
                    <div class="rl-stat" style="padding:0.5rem 0.75rem;">
                        <span class="rl-stat-label">Model</span>
                        <span class="rl-stat-val rl-mono" style="font-size:14px; font-weight:600; margin-top:0.5rem;">{esc(settings.model)}</span>
                    </div>
                    <div class="rl-stat" style="padding:0.5rem 0.75rem;">
                        <span class="rl-stat-label">Elapsed Time</span>
                        <span class="rl-stat-val rl-mono" style="font-size:20px;">{elapsed_s}s</span>
                    </div>
                </div>
            </div>
            """
        )
