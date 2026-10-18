# Redline UI Documentation & Architectural Notes

## 1. Page-to-Reference Mapping

Every screen from the approved reference library in `ui design idea/` was directly mapped and matched in pixel styling:

| UI Screen | Reference Code | Reference Screen | Implementation File | Theme Modes |
|---|---|---|---|---|
| **Home** | `ui design idea/home_redline_private_legal_triage/code.html` | `screen.png` | [`ui/home.py`](file:///c:/Users/anush/Desktop/Hacktoberfest/ZeroLatency/ui/home.py) | Dark (Ink Room) |
| **Auth: Vault** | `ui design idea/vault_local_app_lock/code.html` | `screen.png` | [`ui/auth.py`](file:///c:/Users/anush/Desktop/Hacktoberfest/ZeroLatency/ui/auth.py) | Dark (Ink Room) |
| **Desk** | `ui design idea/desk_document_upload_local_readiness/code.html` | `screen.png` | [`ui/desk.py`](file:///c:/Users/anush/Desktop/Hacktoberfest/ZeroLatency/ui/desk.py) | Dark (Ink Room) |
| **Processing** | `ui design idea/processing_reading_document_local_triage/code.html` | `screen.png` | [`ui/processing.py`](file:///c:/Users/anush/Desktop/Hacktoberfest/ZeroLatency/ui/processing.py) | Dark (Ink Room) |
| **Overview** | `ui design idea/preliminary_overview_redline/code.html` | `screen.png` | [`ui/overview.py`](file:///c:/Users/anush/Desktop/Hacktoberfest/ZeroLatency/ui/overview.py) | Dark & Light |
| **Findings** | `ui design idea/findings_source_viewer/code.html` | `screen.png` | [`ui/findings.py`](file:///c:/Users/anush/Desktop/Hacktoberfest/ZeroLatency/ui/findings.py), [`ui/source_view.py`](file:///c:/Users/anush/Desktop/Hacktoberfest/ZeroLatency/ui/source_view.py) | Dark & Light |
| **Ask the document** | `ui design idea/ask_the_document/code.html` | `screen.png` | [`ui/ask.py`](file:///c:/Users/anush/Desktop/Hacktoberfest/ZeroLatency/ui/ask.py) | Dark & Light |
| **Key facts** | `ui design idea/key_facts_clause_checklist/code.html` | `screen.png` | [`ui/facts.py`](file:///c:/Users/anush/Desktop/Hacktoberfest/ZeroLatency/ui/facts.py) | Dark & Light |
| **Checklist** | `ui design idea/key_facts_clause_checklist/code.html` | `screen.png` | [`ui/checklist.py`](file:///c:/Users/anush/Desktop/Hacktoberfest/ZeroLatency/ui/checklist.py) | Dark & Light |
| **Export** | `ui design idea/export_report_briefings/code.html` | `screen.png` | [`ui/export.py`](file:///c:/Users/anush/Desktop/Hacktoberfest/ZeroLatency/ui/export.py) | Dark & Light |
| **Privacy & model** | `ui design idea/privacy_model_verification/code.html` | `screen.png` | [`ui/privacy_page.py`](file:///c:/Users/anush/Desktop/Hacktoberfest/ZeroLatency/ui/privacy_page.py) | Dark & Light |

---

## 2. Extrapolations (Components without dedicated folders in `ui design idea/`)

1. **Inline Error Cards (`S5`)**:
   - Implemented via `render_error_card()` in [`ui/components.py`](file:///c:/Users/anush/Desktop/Hacktoberfest/ZeroLatency/ui/components.py#L190-L230).
   - Styled with `var(--error-red-bg)` tint, 1px `var(--error-red-border)`, geometric octagon icon, and mono copyable command snippets.
2. **Clear Session & Shred Flow (`F16`)**:
   - Implemented as a confirmation popover in the navigation rail footer with `anim-shred` CSS keyframe slice animation before RAM zeroization and cleanup.
3. **Persistent Disclaimer Component (`F17`)**:
   - Reusable component `render_disclaimer()` placed persistently in the top bar, rail footer, Overview, Ask, and Export.

---

## 3. Strict Safety Adjustments (`frontend.md` Compliance)

In accordance with the conflict rule, any reference mockup elements that conflicted with `frontend.md` safety rules were modified:
1. **No Legal Certainty Claims**: Reference copy referencing "legal", "enforceable", or "valid" was changed to "statutory interpretation" or "syntactic presence in text".
2. **No Red Severity Colors on Findings**: Red is restricted strictly to runtime errors (`error-red`). Finding review requirements use violet (`--review #C3A6FF`), and unverified quotes use terracotta (`--ember #FF9566`).
3. **No Green "Safe" Statuses**: All checklists use neutral ink blue (`#7CC4FF` / `#0F5FA8`) for found wording and neutral dashed circles for unlocated wording.
4. **Verbatim Quote Verification Semantics**: "Verified" badges strictly indicate *"Quote found in document"*, accompanied by the rubber stamp animation (`A3`).
5. **Silent Answer State**: Handled with neutral container styling (`#181612`), explicitly not styled as an error.

---

## 4. Streamlit Limitation Workarounds

1. **Full-Bleed Layouts for Home and Vault**:
   - Streamlit apps typically enforce a fixed sidebar. We resolved this via `inject_theme_css(is_full_bleed=True)`, dynamically applying `display: none !important;` to `[data-testid="stSidebar"]` and expanding `.block-container` to full viewport width when on `Home` or `Auth` routes.
2. **Hover-Expanding Left Rail (72px to 264px)**:
   - Built by styling `[data-testid="stSidebar"]` with `width: 72px !important;` and using CSS transition `:hover, :focus-within` expanding to `264px` with box shadow elevation.
3. **Sticky Source Viewer**:
   - Implemented with CSS `position: sticky; top: 4rem;` on the right-column viewer container, enabling long findings lists to scroll naturally while keeping the source page pinned.
4. **100% Offline Execution**:
   - No external CDNs or font links. All icons are embedded SVGs from `ui/icons.py`. `.streamlit/config.toml` has `gatherUsageStats = false` and `enableStaticServing = true`.
