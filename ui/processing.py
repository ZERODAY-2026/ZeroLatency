"""Processing screen implementation.

Features:
- Centered stage with document preview and moving scan line
- Segment ticks for visual section progress
- Real-time text "Reading section N of M" driven by session.analyze(on_progress)
- Elapsed time and time-to-completion estimate
- Cancel button returning cleanly to the Desk with document kept
- Live execution inside network_guard()
"""

import time
import streamlit as st

from src.errors import AnalysisCancelled
from src.pipeline import DocumentSession
from src.privacy import network_guard

from .components import render_topbar
from .html import render_html, esc
from .state import set_route
from .text import (
    CANCEL_BUTTON_LABEL,
    PROCESSING_CANCELLED_TOAST,
    PROCESSING_DISCLAIMER,
    PROCESSING_SUBTITLE,
    PROCESSING_TITLE,
)


def render_processing() -> None:
    """Render the active analysis processing screen and execute analysis."""
    render_topbar("Processing")

    session: DocumentSession | None = st.session_state.get("session")
    if session is None:
        st.session_state["status"] = "IDLE"
        set_route("Desk")
        st.rerun()
        return

    total_chunks = max(len(session.chunks), 1)

    # Header
    render_html(
        f"""
        <div style="text-align:center; max-width:600px; margin:0 auto; padding:1.5rem 0 1rem 0;">
            <h2 class="rl-card-title" style="font-size:26px; margin-bottom:0.35rem;">{esc(PROCESSING_TITLE)}</h2>
            <p style="font-size:13.5px; color:var(--paper-secondary);">{esc(PROCESSING_SUBTITLE)}</p>
        </div>
        """
    )

    stage_container = st.empty()
    cancel_container = st.empty()

    cancel_requested = False
    with cancel_container:
        col_c1, col_c2, col_c3 = st.columns([5, 2, 5])
        with col_c2:
            if st.button(f"✕ {CANCEL_BUTTON_LABEL}", key="proc_cancel_btn", use_container_width=True):
                cancel_requested = True
                st.session_state["status"] = "READY"
                set_route("Desk")
                st.toast(PROCESSING_CANCELLED_TOAST)
                st.rerun()

    start_time = time.perf_counter()

    def update_ui(current: int, total: int) -> None:
        elapsed = time.perf_counter() - start_time
        mins, secs = int(elapsed // 60), int(elapsed % 60)
        elapsed_str = f"{mins:02d}:{secs:02d}"

        estimate_str = ""
        if current > 0 and total > current:
            avg_per_chunk = elapsed / current
            rem_secs = int(avg_per_chunk * (total - current))
            r_m, r_s = rem_secs // 60, rem_secs % 60
            estimate_str = f"· About {r_m}m {r_s}s left"

        # Generate segment ticks HTML
        ticks_html = []
        for i in range(1, total + 1):
            if i <= current:
                ticks_html.append(
                    '<span style="display:inline-block; width:10px; height:14px; background-color:var(--marker); border-radius:2px;"></span>'
                )
            elif i == current + 1:
                ticks_html.append(
                    '<span style="display:inline-block; width:10px; height:14px; border:1px solid var(--marker); border-radius:2px;"></span>'
                )
            else:
                ticks_html.append(
                    '<span style="display:inline-block; width:10px; height:14px; background-color:var(--line); border-radius:2px;"></span>'
                )
        ticks_block = f'<div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:center; gap:0.35rem; margin:0.75rem auto; max-width:440px;">{"".join(ticks_html)}</div>'

        with stage_container:
            render_html(
                f"""
                <div class="rl-card anim-page-turn" style="max-width:620px; margin:0 auto; padding:1.75rem; text-align:center;">
                    <!-- Scan Line Animation over paper preview -->
                    <div style="position:relative; width:180px; height:220px; margin:0.75rem auto 1.25rem auto; background-color:var(--bg-inset); border:1px solid var(--line); border-radius:8px; overflow:hidden; padding:0.75rem; display:flex; flex-direction:column; justify-content:space-between;">
                        <div class="anim-scan-line"></div>
                        <div style="display:flex; flex-direction:column; gap:0.5rem; opacity:0.3;">
                            <div style="height:8px; background-color:var(--paper-muted); border-radius:3px; width:75%;"></div>
                            <div style="height:8px; background-color:var(--paper-muted); border-radius:3px; width:100%;"></div>
                            <div style="height:8px; background-color:var(--paper-muted); border-radius:3px; width:85%;"></div>
                            <div style="height:8px; background-color:var(--paper-muted); border-radius:3px; width:60%;"></div>
                        </div>
                        <div style="display:flex; flex-direction:column; gap:0.4rem; opacity:0.2;">
                            <div style="height:6px; background-color:var(--paper-muted); border-radius:2px; width:100%;"></div>
                            <div style="height:6px; background-color:var(--paper-muted); border-radius:2px; width:80%;"></div>
                        </div>
                    </div>

                    <div class="rl-card-title" style="font-size:18px; margin-bottom:0.25rem;">
                        Reading section {current} of {total}
                    </div>
                    {ticks_block}
                    <div class="rl-mono" style="font-size:13px; color:var(--paper-muted);">
                        Elapsed {elapsed_str} {estimate_str}
                    </div>

                    <!-- Redaction Cards -->
                    <div style="margin-top:1.5rem; padding-top:1rem; border-top:1px solid var(--line); text-align:left;">
                        <div style="font-size:12px; color:var(--paper-muted); margin-bottom:0.5rem;">{esc(PROCESSING_DISCLAIMER)}</div>
                        <div style="height:14px; background-color:var(--bg-inset); border-radius:4px; width:90%; border:1px solid var(--line); margin-bottom:0.4rem;"></div>
                        <div style="height:14px; background-color:var(--bg-inset); border-radius:4px; width:75%; border:1px solid var(--line); margin-bottom:0.4rem;"></div>
                        <div style="height:14px; background-color:var(--bg-inset); border-radius:4px; width:85%; border:1px solid var(--line);"></div>
                    </div>
                </div>
                """
            )

    update_ui(0, total_chunks)

    def on_progress(done: int, total: int) -> None:
        update_ui(done, total)

    def should_cancel() -> bool:
        return cancel_requested

    observed_network: list[str] = []
    try:
        with network_guard(observed_network):
            result = session.analyze(
                on_progress=on_progress,
                should_cancel=should_cancel,
            )
            st.session_state["result"] = result
            st.session_state["status"] = "DONE"
            st.session_state["error"] = None
            set_route("Overview")
            st.rerun()
    except AnalysisCancelled:
        st.session_state["status"] = "READY"
        set_route("Desk")
        st.toast(PROCESSING_CANCELLED_TOAST)
        st.rerun()
    except Exception as exc:
        err_cls = exc.__class__.__name__
        st.session_state["status"] = "ERROR"
        st.session_state["error"] = (err_cls, str(exc))
        set_route("Desk")
        st.rerun()
