"""Theme CSS injection and design system styles for Redline.

Provides full CSS variables, typography rules, Streamlit overrides,
semantic rl-* component classes, and signature animations for both
Ink Room (dark) and Paper Room (light).
"""

import streamlit as st
from .html import render_html


def inject_theme_css(theme: str = "dark", is_full_bleed: bool = False) -> None:
    """Inject the complete CSS stylesheet into the Streamlit app view."""
    is_dark = theme == "dark"

    # CSS variables for the current theme
    css_vars = f"""
    :root {{
        --bg-app: {'#0D0C0A' if is_dark else '#F5EFE3'};
        --bg-rail: {'#12110E' if is_dark else '#EDE5D4'};
        --bg-surface: {'#181612' if is_dark else '#FFFBF2'};
        --bg-raised: {'#211E19' if is_dark else '#FFFFFF'};
        --bg-inset: {'#0A0908' if is_dark else '#F0E8D8'};
        --line: {'#2C2923' if is_dark else '#E2D8C3'};
        --line-strong: {'#433E34' if is_dark else '#C9BDA3'};
        --paper-primary: {'#F3EDE0' if is_dark else '#1C1A16'};
        --paper-secondary: {'#CFC7B6' if is_dark else '#403B31'};
        --paper-muted: {'#968D7B' if is_dark else '#6B6354'};
        --marker: {'#F7D748' if is_dark else '#F2C500'};
        --marker-dark: {'#1A1608' if is_dark else '#1C1A16'};
        --found: {'#7CC4FF' if is_dark else '#0F5FA8'};
        --found-bg: {'rgba(124, 196, 255, 0.12)' if is_dark else 'rgba(15, 95, 168, 0.10)'};
        --found-border: {'rgba(124, 196, 255, 0.35)' if is_dark else 'rgba(15, 95, 168, 0.30)'};
        --ember: {'#FF9566' if is_dark else '#B8431A'};
        --ember-bg: {'rgba(255, 149, 102, 0.12)' if is_dark else 'rgba(184, 67, 26, 0.10)'};
        --ember-border: {'rgba(255, 149, 102, 0.35)' if is_dark else 'rgba(184, 67, 26, 0.30)'};
        --review: {'#C3A6FF' if is_dark else '#6B3FC9'};
        --review-bg: {'rgba(195, 166, 255, 0.12)' if is_dark else 'rgba(107, 63, 201, 0.10)'};
        --review-border: {'rgba(195, 166, 255, 0.35)' if is_dark else 'rgba(107, 63, 201, 0.30)'};
        --jurisdiction: {'#A9B7C2' if is_dark else '#4B5B68'};
        --jurisdiction-bg: {'rgba(169, 183, 194, 0.12)' if is_dark else 'rgba(75, 91, 104, 0.10)'};
        --local-teal: {'#4FE3C8' if is_dark else '#0B7A6B'};
        --local-teal-bg: {'rgba(79, 227, 200, 0.10)' if is_dark else 'rgba(11, 122, 107, 0.10)'};
        --local-teal-border: {'rgba(79, 227, 200, 0.30)' if is_dark else 'rgba(11, 122, 107, 0.30)'};
        --error-red: {'#FF7A8A' if is_dark else '#B3203A'};
        --error-red-bg: {'rgba(255, 122, 138, 0.10)' if is_dark else 'rgba(179, 32, 58, 0.08)'};
        --error-red-border: {'rgba(255, 122, 138, 0.35)' if is_dark else 'rgba(179, 32, 58, 0.30)'};
    }}
    """

    sidebar_css = (
        """
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="stAppViewContainer"] > .main {
        margin-left: 0 !important;
        padding-left: 0 !important;
    }
    """
        if is_full_bleed
        else """
    /* Stable fixed sidebar (~272px wide, fully expanded) */
    [data-testid="stSidebar"] {
        width: 272px !important;
        min-width: 272px !important;
        max-width: 272px !important;
        background-color: var(--bg-rail) !important;
        border-right: 1px solid var(--line) !important;
        z-index: 100 !important;
        overflow-x: hidden !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        width: 272px !important;
        padding: 1rem 0.85rem !important;
    }
    /* Native collapse button kept visible and styled */
    [data-testid="stSidebarCollapseButton"] {
        display: flex !important;
        visibility: visible !important;
        color: var(--paper-secondary) !important;
    }
    """
    )

    full_css = f"""
    <style>
    {css_vars}

    /* Global Body and App Settings */
    body, html, [data-testid="stAppViewContainer"] {{
        background-color: var(--bg-app) !important;
        color: var(--paper-primary) !important;
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
    }}

    /* Paper grain texture */
    [data-testid="stAppViewContainer"]::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        background-image: radial-gradient(rgba(243, 237, 224, 0.03) 1px, transparent 0);
        background-size: 24px 24px;
        z-index: 1;
        opacity: 0.8;
    }}

    /* Hide Streamlit Header & Toolbar */
    [data-testid="stHeader"] {{
        background-color: transparent !important;
        display: none !important;
    }}
    #MainMenu, footer {{
        visibility: hidden !important;
        height: 0 !important;
    }}

    {sidebar_css}

    /* Main Container Spacing */
    .block-container {{
        max-width: 1380px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        padding-left: {'2rem' if is_full_bleed else '3rem'} !important;
        padding-right: 2rem !important;
        margin: 0 auto !important;
    }}

    /* Typography Classes */
    .font-serif, h1, .rl-hero-title, .rl-card-title, .rl-h1 {{
        font-family: 'Fraunces', Georgia, 'Times New Roman', serif !important;
        font-weight: 600 !important;
        color: var(--paper-primary) !important;
        letter-spacing: -0.02em !important;
    }}
    .font-mono, code, pre, .rl-mono {{
        font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace !important;
    }}
    .rl-eyebrow {{
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--paper-muted);
        font-weight: 600;
    }}

    /* =========================================================================
       SEMANTIC RL-* COMPONENTS
       ========================================================================= */

    /* Native Streamlit Bordered Container Override */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: var(--bg-surface) !important;
        border: 1px solid var(--line) !important;
        border-radius: 14px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] > div {{
        background-color: transparent !important;
    }}

    /* Cards */
    .rl-card {{
        background-color: var(--bg-surface);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 1.25rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        transition: border-color 200ms ease, box-shadow 200ms ease;
        margin-bottom: 1rem;
    }}
    .rl-card-selected {{
        border-left: 3px solid var(--marker) !important;
        background-color: var(--bg-raised) !important;
    }}
    .rl-card-title {{
        font-size: 17px;
        font-weight: 600;
        color: var(--paper-primary);
        margin-bottom: 0.5rem;
        display: block;
    }}
    .rl-card-sub {{
        font-size: 13px;
        color: var(--paper-secondary);
        line-height: 1.5;
        margin-bottom: 0.75rem;
    }}
    .rl-card-body {{
        font-size: 13px;
        color: var(--paper-secondary);
        line-height: 1.6;
    }}

    /* Card Grids */
    .rl-grid-2 {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1.25rem;
        margin-bottom: 1.25rem;
    }}
    .rl-grid-3 {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1.25rem;
        margin-bottom: 1.25rem;
    }}
    .rl-grid-4 {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 1rem;
        margin-bottom: 1.25rem;
    }}
    @media (max-width: 900px) {{
        .rl-grid-3, .rl-grid-4 {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }}
    }}
    @media (max-width: 640px) {{
        .rl-grid-2, .rl-grid-3, .rl-grid-4 {{
            grid-template-columns: 1fr;
        }}
    }}

    /* Badges */
    .rl-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        height: 26px;
        padding: 0 0.75rem;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 550;
        line-height: 1;
        border: 1px solid var(--line);
        background-color: var(--bg-raised);
        color: var(--paper-secondary);
        white-space: nowrap;
    }}
    .rl-badge-verified {{
        background-color: var(--found-bg) !important;
        border-color: var(--found-border) !important;
        color: var(--found) !important;
    }}
    .rl-badge-unverified {{
        background-color: var(--ember-bg) !important;
        border-color: var(--ember-border) !important;
        color: var(--ember) !important;
    }}
    .rl-badge-review {{
        background-color: var(--review-bg) !important;
        border-color: var(--review-border) !important;
        color: var(--review) !important;
    }}
    .rl-badge-jurisdiction {{
        background-color: var(--jurisdiction-bg) !important;
        border-color: var(--line) !important;
        color: var(--jurisdiction) !important;
    }}
    .rl-badge-local {{
        background-color: var(--local-teal-bg) !important;
        border-color: var(--local-teal-border) !important;
        color: var(--local-teal) !important;
    }}
    .rl-badge-neutral {{
        background-color: var(--bg-inset) !important;
        border-color: var(--line) !important;
        color: var(--paper-secondary) !important;
    }}

    /* Quote Blocks */
    .rl-quote {{
        background-color: var(--bg-inset);
        border: 1px solid var(--line);
        border-left: 3px solid var(--found);
        border-radius: 6px;
        padding: 0.85rem 1rem;
        font-family: 'JetBrains Mono', Consolas, monospace;
        font-size: 13px;
        line-height: 1.6;
        color: var(--paper-primary);
        margin: 0.75rem 0;
        position: relative;
    }}
    .rl-quote-unverified {{
        border-left: 3px dashed var(--ember) !important;
    }}

    /* Tables (real <table> component) */
    .rl-table-container {{
        width: 100%;
        overflow-x: auto;
        border: 1px solid var(--line);
        border-radius: 10px;
        background-color: var(--bg-surface);
        margin: 0.75rem 0 1.25rem 0;
    }}
    table.rl-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        text-align: left;
    }}
    table.rl-table th {{
        background-color: var(--bg-inset);
        color: var(--paper-muted);
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--line);
        position: sticky;
        top: 0;
    }}
    table.rl-table td {{
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--line);
        color: var(--paper-secondary);
        line-height: 1.4;
    }}
    table.rl-table tr:last-child td {{
        border-bottom: none;
    }}
    table.rl-table tr:hover td {{
        background-color: var(--bg-raised);
    }}
    table.rl-table td.rl-mono {{
        font-family: 'JetBrains Mono', Consolas, monospace;
        font-size: 12px;
        color: var(--paper-primary);
    }}

    /* Stats Cards */
    .rl-stat {{
        display: flex;
        flex-direction: column;
        padding: 0.85rem 1rem;
        background-color: var(--bg-raised);
        border: 1px solid var(--line);
        border-radius: 10px;
    }}
    .rl-stat-label {{
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--paper-muted);
    }}
    .rl-stat-val {{
        font-family: 'Fraunces', Georgia, serif;
        font-size: 30px;
        font-weight: 600;
        line-height: 1.1;
        margin-top: 0.35rem;
        color: var(--paper-primary);
    }}

    /* Stepper */
    .rl-stepper {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1.25rem;
        margin: 1.5rem 0;
    }}
    @media (max-width: 768px) {{
        .rl-stepper {{
            grid-template-columns: 1fr;
        }}
    }}
    .rl-step {{
        display: flex;
        flex-direction: column;
        padding: 1.25rem;
        background-color: var(--bg-surface);
        border: 1px solid var(--line);
        border-radius: 12px;
    }}
    .rl-step-num {{
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background-color: var(--bg-inset);
        border: 1px solid var(--line-strong);
        color: var(--paper-primary);
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 0.75rem;
    }}
    .rl-step-title {{
        font-size: 15px;
        font-weight: 600;
        color: var(--paper-primary);
        margin-bottom: 0.35rem;
    }}
    .rl-step-desc {{
        font-size: 13px;
        color: var(--paper-secondary);
        line-height: 1.5;
    }}

    /* Key-Value Status Rows */
    .rl-kv-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.6rem 0;
        border-bottom: 1px solid var(--line);
        font-size: 13px;
    }}
    .rl-kv-row:last-child {{
        border-bottom: none;
    }}
    .rl-kv-label {{
        color: var(--paper-muted);
    }}
    .rl-kv-val {{
        color: var(--paper-primary);
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    /* Chips */
    .rl-chip {{
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.35rem 0.65rem;
        border-radius: 8px;
        background-color: var(--bg-surface);
        border: 1px solid var(--line);
        font-size: 12px;
        color: var(--paper-secondary);
    }}

    /* Callouts */
    .rl-callout {{
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.85rem 1.1rem;
        background-color: var(--bg-inset);
        border: 1px solid var(--line);
        border-radius: 10px;
        color: var(--paper-secondary);
        font-size: 13px;
        line-height: 1.5;
        margin: 1rem 0;
    }}

    /* Hero Section */
    .rl-hero {{
        padding: 1.5rem 0 2rem 0;
    }}
    .rl-hero-title {{
        font-size: 44px;
        line-height: 1.15;
        margin: 0.75rem 0 1rem 0;
    }}
    .rl-hero-highlight {{
        position: relative;
        display: inline-block;
        white-space: nowrap;
    }}
    .rl-hero-highlight::after {{
        content: "";
        position: absolute;
        left: 0;
        bottom: 4px;
        width: 100%;
        height: 12px;
        background-color: rgba(247, 215, 72, 0.3);
        border-radius: 2px;
        z-index: -1;
    }}
    .rl-hero-sub {{
        font-size: 16px;
        color: var(--paper-secondary);
        line-height: 1.6;
        max-width: 600px;
        margin-bottom: 1.25rem;
    }}

    /* Empty States */
    .rl-empty-state {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 3.5rem 2rem;
        text-align: center;
        background-color: var(--bg-surface);
        border: 1px dashed var(--line-strong);
        border-radius: 14px;
        margin: 1.5rem 0;
    }}
    .rl-empty-icon {{
        font-size: 36px;
        margin-bottom: 1rem;
        opacity: 0.8;
    }}
    .rl-empty-title {{
        font-size: 18px;
        font-weight: 600;
        color: var(--paper-primary);
        margin-bottom: 0.5rem;
    }}
    .rl-empty-desc {{
        font-size: 14px;
        color: var(--paper-muted);
        max-width: 440px;
        line-height: 1.5;
        margin-bottom: 1.5rem;
    }}

    /* Sidebar Brand & Top Sections */
    .rl-sidebar-brand {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding-bottom: 0.85rem;
        border-bottom: 1px solid var(--line);
        margin-bottom: 0.75rem;
        cursor: pointer;
    }}
    .rl-sidebar-brand-title {{
        font-family: 'Fraunces', Georgia, serif;
        font-size: 18px;
        font-weight: 600;
        color: var(--paper-primary);
        line-height: 1.1;
    }}
    .rl-sidebar-brand-sub {{
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--paper-muted);
        margin-top: 2px;
    }}
    .rl-sidebar-badge {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.5rem 0.65rem;
        background-color: var(--bg-surface);
        border: 1px solid var(--line);
        border-radius: 8px;
        margin-bottom: 0.75rem;
        font-size: 11px;
    }}
    .rl-sidebar-doc {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0.65rem;
        background-color: var(--bg-inset);
        border: 1px solid var(--line);
        border-radius: 8px;
        margin-bottom: 1rem;
        font-size: 12px;
        color: var(--paper-secondary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    /* Divider */
    .rl-divider {{
        height: 1px;
        background-color: var(--line);
        margin: 1.5rem 0;
    }}

    /* Disclaimers */
    .rl-disclaimer {{
        font-size: 12px;
        color: var(--paper-muted);
        line-height: 1.5;
        padding: 0.75rem 0;
    }}

    /* Native Streamlit Buttons Override */
    .stButton > button {{
        background-color: var(--bg-raised) !important;
        color: var(--paper-primary) !important;
        border: 1px solid var(--line-strong) !important;
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 550 !important;
        font-size: 14px !important;
        transition: all 180ms ease !important;
        cursor: pointer !important;
    }}
    .stButton > button:hover {{
        background-color: var(--line) !important;
        border-color: var(--paper-muted) !important;
        transform: translateY(-1px) !important;
    }}
    .stButton > button:active {{
        transform: scale(0.98) !important;
    }}
    /* Primary Button (Marker Yellow) */
    .stButton > button[kind="primary"], .rl-btn-primary {{
        background-color: var(--marker) !important;
        color: var(--marker-dark) !important;
        border: 1px solid var(--marker) !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2) !important;
    }}
    .stButton > button[kind="primary"]:hover, .rl-btn-primary:hover {{
        filter: brightness(1.05) !important;
        transform: translateY(-1px) !important;
    }}

    /* Sidebar Navigation Button Active State */
    [class*="st-key-nav_"] button {{
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 13.5px !important;
        border: 1px solid transparent !important;
        background-color: transparent !important;
        border-radius: 8px !important;
        padding: 0.45rem 0.65rem !important;
        color: var(--paper-secondary) !important;
    }}
    [class*="st-key-nav_"] button:hover {{
        background-color: var(--bg-surface) !important;
        color: var(--paper-primary) !important;
    }}
    /* Active Nav Item Styling */
    .rl-nav-active button {{
        background-color: var(--bg-raised) !important;
        border-left: 3px solid var(--marker) !important;
        border-color: var(--line) !important;
        color: var(--paper-primary) !important;
        font-weight: 700 !important;
    }}

    /* Inputs override */
    .stTextInput > div > div > input, .stTextArea textarea, .stSelectbox select {{
        background-color: var(--bg-raised) !important;
        color: var(--paper-primary) !important;
        border: 1px solid var(--line-strong) !important;
        border-radius: 10px !important;
        font-size: 14px !important;
    }}
    .stTextInput > div > div > input:focus, .stTextArea textarea:focus {{
        border-color: var(--marker) !important;
        box-shadow: 0 0 0 1px var(--marker) !important;
    }}

    /* Native dropzone override */
    [data-testid="stFileUploader"] {{
        background-color: var(--bg-surface) !important;
        border: 2px dashed var(--line-strong) !important;
        border-radius: 14px !important;
        padding: 1.5rem !important;
        transition: border-color 220ms ease !important;
    }}
    [data-testid="stFileUploader"]:hover {{
        border-color: var(--marker) !important;
    }}

    /* =========================================================================
       ANIMATIONS (Wrapped in prefers-reduced-motion)
       ========================================================================= */
    @media (prefers-reduced-motion: no-preference) {{
        .anim-page-turn {{
            animation: a1PageTurn 220ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }}
        @keyframes a1PageTurn {{
            from {{ opacity: 0; transform: translateY(12px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .anim-scan-line {{
            position: absolute;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--marker), transparent);
            box-shadow: 0 0 10px var(--marker);
            animation: a4Scan 2.4s ease-in-out infinite;
        }}
        @keyframes a4Scan {{
            0% {{ top: 0%; opacity: 0.8; }}
            50% {{ opacity: 1; }}
            100% {{ top: 100%; opacity: 0.8; }}
        }}

        .anim-orbit {{
            animation: a6Orbit 14s linear infinite;
        }}
        @keyframes a6Orbit {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}

        .anim-breathing-dot {{
            animation: a14Breathe 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }}
        @keyframes a14Breathe {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.45; transform: scale(0.9); }}
        }}
    }}
    </style>
    """
    render_html(full_css)
