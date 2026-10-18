"""Auth: 'Vault' local app lock implementation.

Features:
- Full-bleed centered vault card
- Mechanical segmented dial
- Local salted hash verification using hashlib.pbkdf2_hmac
- First-run setup with strength meter
- Returning unlock with lockout countdown
- Reset session dialog clearing temporary files
- Safe HTML rendering with semantic rl-* classes
"""

import hashlib
import json
import os
import time
from pathlib import Path
import streamlit as st

from .html import render_html, esc
from .icons import svg_icon
from .state import clear_session, set_route
from .text import (
    VAULT_DESC_LOCAL_LOCK,
    VAULT_RESET_WARNING,
    VAULT_SUBTITLE_SETRUN,
    VAULT_SUBTITLE_UNLOCK,
    VAULT_TITLE_SETRUN,
    VAULT_TITLE_UNLOCK,
)

CONFIG_FILE = Path(__file__).parent.parent / ".vault_lock.json"


def _hash_passphrase(passphrase: str, salt: bytes | None = None) -> tuple[str, str]:
    """Compute salted PBKDF2 HMAC SHA256 hash."""
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 100000)
    return key.hex(), salt.hex()


def _verify_passphrase(passphrase: str, saved_hash: str, saved_salt: str) -> bool:
    """Verify passphrase against stored salt and hash."""
    salt = bytes.fromhex(saved_salt)
    key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 100000)
    return key.hex() == saved_hash


def render_auth() -> None:
    """Render the Vault local app lock page."""
    saved_cfg = {}
    if CONFIG_FILE.exists():
        try:
            saved_cfg = json.loads(CONFIG_FILE.read_text())
        except Exception:
            saved_cfg = {}

    is_first_run = not saved_cfg.get("enabled", False)

    # Top Minimal Bar
    render_html(
        f"""
        <div style="display:flex; align-items:center; justify-content:space-between; padding-bottom:1.5rem; margin-bottom:1.5rem; border-bottom:1px solid var(--line);">
            <div style="display:flex; align-items:center; gap:0.5rem;">
                <div style="width:32px; height:32px; border-radius:8px; background:var(--bg-raised); border:1px solid var(--line); display:flex; align-items:center; justify-content:center;">
                    {svg_icon("lock", 16, "var(--paper-primary)")}
                </div>
                <span class="rl-mono" style="font-weight:600; font-size:14px; color:var(--paper-primary);">VAULT // LOCAL</span>
            </div>
            <div class="rl-badge rl-badge-local">
                <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background-color:var(--local-teal);" class="anim-breathing-dot"></span>
                <span>LOCAL SCREEN LOCK</span>
            </div>
        </div>
        """
    )

    # Centered Vault Card (440px)
    col_l, col_center, col_r = st.columns([1, 2, 1])

    with col_center:
        title_text = VAULT_TITLE_SETRUN if is_first_run else VAULT_TITLE_UNLOCK
        subtitle_text = VAULT_SUBTITLE_SETRUN if is_first_run else VAULT_SUBTITLE_UNLOCK

        render_html(
            f"""
            <div class="rl-card anim-page-turn" style="text-align:center; padding:1.75rem;">
                <!-- Mechanical Segmented Vault Dial -->
                <div style="position:relative; width:80px; height:80px; margin:0 auto 1rem auto; display:flex; align-items:center; justify-content:center;">
                    <svg width="80" height="80" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="50" cy="50" r="46" stroke="var(--line-strong)" stroke-width="1.2" stroke-dasharray="2 4"/>
                        <circle cx="50" cy="50" r="41" stroke="var(--line)" stroke-width="1"/>
                        <circle cx="50" cy="50" r="34" stroke="var(--marker)" stroke-width="2.5" stroke-dasharray="28 8 28 8 28 8" stroke-linecap="round"/>
                        <circle cx="50" cy="50" r="16" fill="var(--bg-inset)" stroke="var(--line-strong)" stroke-width="1.5"/>
                    </svg>
                    <div style="position:absolute; inset:0; display:flex; align-items:center; justify-content:center; color:var(--marker);">
                        {svg_icon("shield", 20, "var(--marker)")}
                    </div>
                </div>
                <h1 class="rl-card-title" style="font-size:22px; margin-bottom:0.35rem;">
                    {esc(title_text)}
                </h1>
                <p style="font-size:13px; color:var(--paper-secondary); line-height:1.5;">
                    {esc(subtitle_text)}
                </p>
            </div>
            """
        )

        if is_first_run:
            p1 = st.text_input("Enter Passphrase", type="password", key="vault_setup_p1")
            p2 = st.text_input("Confirm Passphrase", type="password", key="vault_setup_p2")

            # Strength Meter
            if p1:
                strength_label, strength_color = ("Weak", "var(--ember)")
                if len(p1) >= 8 and any(c.isdigit() for c in p1):
                    strength_label, strength_color = ("Strong", "var(--local-teal)")
                elif len(p1) >= 6:
                    strength_label, strength_color = ("Okay", "var(--marker)")

                render_html(
                    f'<div style="font-size:12px; margin:0.35rem 0; color:{strength_color};">Strength: <strong>{esc(strength_label)}</strong></div>'
                )

            col_set, col_skip = st.columns([1, 1])
            with col_set:
                if st.button("Set passphrase", type="primary", use_container_width=True):
                    if not p1:
                        st.error("Please enter a passphrase.")
                    elif p1 != p2:
                        st.error("Passphrases do not match.")
                    else:
                        h_val, s_val = _hash_passphrase(p1)
                        CONFIG_FILE.write_text(json.dumps({"enabled": True, "hash": h_val, "salt": s_val}))
                        st.session_state["vault_enabled"] = True
                        st.session_state["auth_ok"] = True
                        set_route("Desk")
                        st.toast("Passphrase set. Screen locked to this computer.")
                        st.rerun()

            with col_skip:
                if st.button("Skip, I am sole user", use_container_width=True):
                    st.session_state["vault_enabled"] = False
                    st.session_state["auth_ok"] = True
                    set_route("Desk")
                    st.rerun()

        else:
            pass_input = st.text_input("Enter passphrase", type="password", key="vault_unlock_input")

            attempts = st.session_state.get("vault_attempts", 0)
            locked_until = st.session_state.get("vault_locked_until", 0)
            now = time.time()

            if now < locked_until:
                st.warning(f"Too many attempts. Locked for {int(locked_until - now)} more seconds.")
            else:
                if st.button("Unlock Redline", type="primary", use_container_width=True):
                    saved_hash = saved_cfg.get("hash", "")
                    saved_salt = saved_cfg.get("salt", "")

                    if _verify_passphrase(pass_input, saved_hash, saved_salt):
                        st.session_state["auth_ok"] = True
                        st.session_state["vault_attempts"] = 0
                        set_route("Desk")
                        st.rerun()
                    else:
                        st.session_state["vault_attempts"] = attempts + 1
                        if st.session_state["vault_attempts"] >= 3:
                            st.session_state["vault_locked_until"] = time.time() + 5
                        st.error("That passphrase didn't match. Try again.")

            with st.popover("Forgot passphrase? Reset session", use_container_width=True):
                render_html(
                    f'<p style="font-size:13px; color:var(--paper-secondary); line-height:1.5; margin-bottom:0.75rem;">{esc(VAULT_RESET_WARNING)}</p>'
                )
                if st.button("Reset lock & wipe session", type="primary", use_container_width=True):
                    if CONFIG_FILE.exists():
                        CONFIG_FILE.unlink()
                    clear_session()
                    st.session_state["vault_enabled"] = False
                    st.session_state["auth_ok"] = True
                    set_route("Desk")
                    st.rerun()

        render_html(
            f"""
            <div style="margin-top:1.5rem; padding-top:1rem; border-top:1px solid var(--line); text-align:center; font-size:12px; color:var(--paper-muted); line-height:1.5;">
                {esc(VAULT_DESC_LOCAL_LOCK)}
            </div>
            """
        )
