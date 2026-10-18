"""Desk page implementation (upload and readiness check).

Features:
- Live readiness check banner from OllamaClient.check_ready() with copyable commands
- Upload dropzone for PDF and TXT files up to 50 MB
- "Use sample document" demo loader for samples/rental_agreement.pdf
- "Tested on" contract categories panel
- Parsed document card: file name, page count, character count, sparse page warning, file type
- Primary "Analyse document" action button (disabled with clear explanation if model not ready)
- Safe HTML rendering with semantic rl-* classes
"""

from pathlib import Path
import streamlit as st

from src.config import settings
from src.document_parser import low_text_pages
from src.pipeline import DocumentSession
from src.privacy import PrivateWorkspace, network_guard

from .components import render_error_card, render_topbar
from .html import render_html, esc
from .icons import svg_icon
from .state import check_ollama_readiness, set_route
from .text import (
    ANALYSE_BUTTON_LABEL,
    ANALYSE_DISABLED_MODEL_NOT_READY,
    DESK_SUBTITLE,
    DESK_TITLE,
    DROPZONE_LIMIT,
    SAMPLE_BUTTON_LABEL,
    SPARSE_PAGE_WARNING,
    TESTED_ON_DOCUMENTS,
)

SAMPLE_PATH = Path(__file__).parent.parent / "private-legal-triage" / "samples" / "rental_agreement.pdf"


def load_sample_document() -> None:
    """Helper to load the sample rental agreement onto the desk."""
    if SAMPLE_PATH.exists():
        _process_file_upload(SAMPLE_PATH.name, SAMPLE_PATH.read_bytes())
    else:
        raise FileNotFoundError("Sample document not found at samples/rental_agreement.pdf")


def render_desk() -> None:
    """Render the main Desk page."""
    render_topbar("Desk")

    # Desk Header
    render_html(
        f"""
        <div style="display:flex; flex-wrap:wrap; align-items:flex-end; justify-content:space-between; gap:1rem; padding-bottom:1rem; border-bottom:1px solid var(--line); margin-bottom:1.5rem;">
            <div>
                <div class="rl-badge rl-badge-local" style="margin-bottom:0.5rem;">
                    <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background-color:var(--local-teal);" class="anim-breathing-dot"></span>
                    <span>Local only · Private temporary folder · No cloud</span>
                </div>
                <h1 class="rl-hero-title" style="font-size:32px; margin:0.25rem 0;">{esc(DESK_TITLE)}</h1>
                <p style="font-size:14px; color:var(--paper-secondary);">{esc(DESK_SUBTITLE)}</p>
            </div>
            <div class="rl-mono" style="font-size:11px; color:var(--paper-muted); text-align:right;">
                <span style="color:var(--paper-secondary); font-weight:600;">REDLINE STATION · LOCAL EXECUTION</span><br/>
                LOOPBACK PROCESSING ONLY
            </div>
        </div>
        """
    )

    # 1. Readiness Banner
    is_ready, ready_msg, fix_cmd = check_ollama_readiness()

    if is_ready:
        render_html(
            f"""
            <div class="rl-card" style="border-color:var(--local-teal-border); padding:1rem 1.25rem; margin-bottom:1.5rem;">
                <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:0.75rem;">
                    <div style="display:flex; align-items:center; gap:0.75rem;">
                        <div style="width:36px; height:36px; border-radius:8px; background:var(--bg-inset); border:1px solid var(--local-teal-border); display:flex; align-items:center; justify-content:center; color:var(--local-teal); flex-shrink:0;">
                            {svg_icon("shield_lock", 20, "var(--local-teal)")}
                        </div>
                        <div>
                            <div style="display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap;">
                                <span style="font-weight:600; color:var(--paper-primary); font-size:14.5px;">Local model ready</span>
                                <span style="color:var(--line-strong);">·</span>
                                <span class="rl-mono" style="color:var(--local-teal); font-weight:600; font-size:13px;">{esc(settings.model)}</span>
                                <span style="color:var(--paper-muted); font-size:13px;">on Ollama</span>
                                <span class="rl-mono" style="font-size:11px; padding:0.1rem 0.35rem; background:var(--bg-inset); border-radius:4px; border:1px solid var(--line); color:var(--paper-secondary);">127.0.0.1:11434</span>
                            </div>
                            <div style="display:flex; align-items:center; gap:0.5rem; font-size:12px; color:var(--paper-muted); margin-top:2px;">
                                <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background-color:var(--local-teal);" class="anim-breathing-dot"></span>
                                <span>Offline & responsive</span>
                                <span>·</span>
                                <span>Context window: {settings.num_ctx // 1024}k tokens</span>
                                <span>·</span>
                                <span>Zero external network traffic</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
        )
    else:
        cmd_box = f'<div class="rl-mono" style="font-size:12px; padding:0.5rem 0.75rem; margin:0.4rem 0; border-radius:6px; background:var(--bg-inset); border:1px solid var(--line); color:var(--paper-primary);"><code>{esc(fix_cmd)}</code></div>' if fix_cmd else ""
        render_html(
            f"""
            <div class="rl-card" style="border-color:var(--ember-border); padding:1rem 1.25rem; margin-bottom:1.5rem;">
                <div style="display:flex; align-items:flex-start; gap:0.75rem;">
                    <div style="width:36px; height:36px; border-radius:8px; background:var(--ember-bg); border:1px solid var(--ember-border); display:flex; align-items:center; justify-content:center; color:var(--ember); flex-shrink:0;">
                        {svg_icon("triangle_alert", 20, "var(--ember)")}
                    </div>
                    <div>
                        <div style="font-weight:600; color:var(--ember); font-size:14.5px;">{esc(ready_msg)}</div>
                        <div style="font-size:13px; color:var(--paper-secondary); margin-top:2px;">The local model is required to analyse documents offline.</div>
                        {cmd_box}
                        <div style="font-size:12px; color:var(--paper-muted); margin-top:0.25rem;">Start Ollama locally on 127.0.0.1:11434 to proceed.</div>
                    </div>
                </div>
            </div>
            """
        )

    # 2. Workspace: Dropzone and Tested-on side panel
    col_left, col_right = st.columns([7, 5], gap="large")

    with col_left:
        render_html(
            '<div class="rl-card-title" style="font-size:17px; margin-bottom:0.5rem;">Upload document</div>'
        )

        uploaded_file = st.file_uploader(
            label="Drop a PDF or TXT here",
            type=["pdf", "txt"],
            help=DROPZONE_LIMIT,
            key="desk_uploader",
        )

        if uploaded_file is not None:
            current_name = st.session_state.get("doc_name")
            if current_name != uploaded_file.name:
                _process_file_upload(uploaded_file.name, uploaded_file.getvalue())

        session: DocumentSession | None = st.session_state.get("session")
        doc_path: Path | None = st.session_state.get("path")
        doc_name: str | None = st.session_state.get("doc_name")

        if session is not None and doc_path is not None and doc_name is not None:
            pages_count = len(session.pages)
            total_chars = sum(len(p.text) for p in session.pages)
            sparse_pages = low_text_pages(session.pages, session.cfg)
            file_type = doc_path.suffix.upper().lstrip(".")

            sparse_warning_html = ""
            if sparse_pages:
                sparse_warning_html = f"""
                <div class="rl-callout" style="background-color:var(--ember-bg); border-color:var(--ember-border); color:var(--ember); margin-top:0.75rem;">
                    {svg_icon("triangle_alert", 15, "var(--ember)")}
                    <span>{esc(SPARSE_PAGE_WARNING)} Pages: {', '.join(map(str, sparse_pages))}</span>
                </div>
                """

            render_html(
                f"""
                <div class="rl-card anim-page-turn" style="margin:1rem 0;">
                    <div style="display:flex; align-items:flex-start; justify-content:space-between; border-bottom:1px solid var(--line); padding-bottom:0.75rem; margin-bottom:0.75rem;">
                        <div style="display:flex; align-items:center; gap:0.75rem;">
                            <div style="width:36px; height:36px; border-radius:8px; background:var(--bg-raised); border:1px solid var(--line); display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                                {svg_icon("description", 20, "var(--paper-primary)")}
                            </div>
                            <div>
                                <div class="rl-mono" style="font-weight:600; font-size:14.5px; color:var(--paper-primary);">{esc(doc_name)}</div>
                                <div style="font-size:12px; color:var(--paper-muted);">Ready on desk · {file_type} Document</div>
                            </div>
                        </div>
                        <span class="rl-badge rl-badge-local" style="font-size:11px;">
                            Ready
                        </span>
                    </div>
                    <div class="rl-grid-4" style="margin-bottom:0.25rem; text-align:center;">
                        <div class="rl-stat" style="padding:0.5rem;">
                            <span class="rl-stat-label">Pages</span>
                            <span class="rl-stat-val" style="font-size:18px;">{pages_count}</span>
                        </div>
                        <div class="rl-stat" style="padding:0.5rem;">
                            <span class="rl-stat-label">Characters</span>
                            <span class="rl-stat-val" style="font-size:18px;">{total_chars:,}</span>
                        </div>
                        <div class="rl-stat" style="padding:0.5rem;">
                            <span class="rl-stat-label">Low Text</span>
                            <span class="rl-stat-val" style="font-size:18px; color:{'var(--ember)' if sparse_pages else 'var(--paper-primary)'};">{len(sparse_pages)}</span>
                        </div>
                        <div class="rl-stat" style="padding:0.5rem;">
                            <span class="rl-stat-label">Sections</span>
                            <span class="rl-stat-val" style="font-size:18px;">{len(session.chunks)}</span>
                        </div>
                    </div>
                    {sparse_warning_html}
                </div>
                """
            )

            analyse_disabled = not is_ready
            help_text = ANALYSE_DISABLED_MODEL_NOT_READY if analyse_disabled else None

            if st.button(
                f"⚡ {ANALYSE_BUTTON_LABEL}",
                key="desk_analyse_btn",
                type="primary",
                disabled=analyse_disabled,
                help=help_text,
                use_container_width=True,
            ):
                st.session_state["status"] = "ANALYZING"
                set_route("Overview")
                st.rerun()

        # Display parse error if any
        err = st.session_state.get("error")
        if err is not None:
            err_cls, err_msg = err
            render_error_card(err_cls, message=err_msg)

    with col_right:
        items_html = "".join(
            f'<div style="display:flex; align-items:center; gap:0.5rem; font-size:13px; color:var(--paper-secondary); padding:0.4rem 0; border-bottom:1px solid var(--line);">{svg_icon("check", 14, "var(--local-teal)")} <span>{esc(item)}</span></div>'
            for item in TESTED_ON_DOCUMENTS
        )

        render_html(
            f"""
            <div class="rl-card">
                <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.5rem;">
                    {svg_icon("check_circle", 16, "var(--local-teal)")}
                    <span class="rl-card-title" style="font-size:16px; margin-bottom:0;">Tested document categories</span>
                </div>
                <p style="font-size:13px; color:var(--paper-muted); line-height:1.5; margin-bottom:0.75rem;">
                    Redline's triage prompts are calibrated and benchmarked against standard commercial and civil contracts:
                </p>
                <div>
                    {items_html}
                </div>
            </div>
            """
        )

        # Sample Document Loader Button
        render_html(
            """
            <div class="rl-card" style="margin-top:1rem;">
                <div class="rl-card-title" style="font-size:16px; margin-bottom:0.35rem;">Try a demo document</div>
                <p style="font-size:13px; color:var(--paper-muted); line-height:1.5; margin-bottom:0.75rem;">
                    Load an offline residential rental agreement containing standard renewal, notice, and deposit clauses.
                </p>
            </div>
            """
        )

        if st.button(
            f"📄 {SAMPLE_BUTTON_LABEL}",
            key="desk_load_sample_btn",
            use_container_width=True,
        ):
            if SAMPLE_PATH.exists():
                _process_file_upload(SAMPLE_PATH.name, SAMPLE_PATH.read_bytes())
                st.toast("Loaded sample rental agreement onto the desk.")
                st.rerun()
            else:
                st.error("Sample document not found at samples/rental_agreement.pdf")


def _process_file_upload(filename: str, data: bytes) -> None:
    """Save upload to PrivateWorkspace and initialize DocumentSession inside network_guard()."""
    workspace: PrivateWorkspace | None = st.session_state.get("workspace")
    if workspace is None:
        workspace = PrivateWorkspace()
        workspace.__enter__()
        st.session_state["workspace"] = workspace

    observed: list[str] = []
    try:
        with network_guard(observed):
            target_path = workspace.save_upload(filename, data)
            session = DocumentSession(target_path, cfg=settings)
            st.session_state["status"] = "READY"
            st.session_state["path"] = target_path
            st.session_state["doc_name"] = filename
            st.session_state["session"] = session
            st.session_state["result"] = None
            st.session_state["answers"] = []
            st.session_state["selected_finding"] = None
            st.session_state["viewer_page"] = 1
            st.session_state["error"] = None
    except Exception as exc:
        err_cls = exc.__class__.__name__
        st.session_state["status"] = "ERROR"
        st.session_state["error"] = (err_cls, str(exc))
        st.session_state["session"] = None
