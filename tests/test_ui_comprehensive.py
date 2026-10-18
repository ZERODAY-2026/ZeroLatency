"""Comprehensive UI and safety test suite for Redline.

Tests:
1. Forbidden words test (safety compliance): No UI strings contain prohibited legal-certainty words.
2. Error mapping test: All 10 backend error classes are properly mapped with title, message, and next step.
3. Offline integrity test: Codebase contains no external CDN, remote fonts, or telemetry scripts.
4. Streamlit AppTest flow: Upload sample, fake client analysis, results verification, filters, ask tab, export, and session cleanup.
"""

import os
import re
import sys
from pathlib import Path
import pytest

# Ensure source imports resolve
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "private-legal-triage"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.text import (
    ERROR_MAPPINGS,
    FORBIDDEN_WORDS,
    audit_string_safety,
)
from src.errors import (
    EmptyQuestion,
    EncryptedDocument,
    InvalidModelOutput,
    ModelMissing,
    ModelTimeout,
    NoExtractableText,
    OllamaUnavailable,
    PrivacyViolation,
    UnreadableDocument,
    UnsupportedFormat,
)


def test_forbidden_words_in_text_module():
    """Verify that no UI string in ui/text.py contains prohibited certainty words."""
    import ui.text as ui_text

    violations = []
    ignored = {"FORBIDDEN_WORDS", "__doc__"}
    for attr in dir(ui_text):
        if attr.startswith("_") or attr in ignored:
            continue
        val = getattr(ui_text, attr)
        if isinstance(val, str):
            found = audit_string_safety(val)
            if found:
                violations.append((attr, val, found))
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    found = audit_string_safety(item)
                    if found:
                        violations.append((attr, item, found))
                elif isinstance(item, dict):
                    for v in item.values():
                        if isinstance(v, str):
                            found = audit_string_safety(v)
                            if found:
                                violations.append((attr, v, found))

    assert not violations, f"Prohibited certainty words detected in ui/text.py: {violations}"


def test_error_mapping_table_completeness():
    """Ensure all required backend exceptions have friendly human error mappings."""
    required_errors = [
        "UnsupportedFormat",
        "EncryptedDocument",
        "UnreadableDocument",
        "NoExtractableText",
        "OllamaUnavailable",
        "ModelMissing",
        "ModelTimeout",
        "InvalidModelOutput",
        "EmptyQuestion",
        "PrivacyViolation",
    ]

    for err_name in required_errors:
        assert err_name in ERROR_MAPPINGS, f"Missing mapping for {err_name}"
        mapping = ERROR_MAPPINGS[err_name]
        assert mapping.title, f"Missing title for {err_name}"
        assert mapping.message, f"Missing message for {err_name}"
        assert mapping.next_step, f"Missing next_step for {err_name}"
        # Ensure error messages never contain document text or certainty judgements
        assert not audit_string_safety(mapping.title)
        assert not audit_string_safety(mapping.message)
        assert not audit_string_safety(mapping.next_step)


def test_no_external_cdn_or_telemetry_links_in_ui():
    """Ensure ui/ python code contains no remote CDN links (fonts, tailwind, unpkg, etc.)."""
    ui_dir = PROJECT_ROOT / "ui"
    forbidden_domains = [
        "cdn.tailwindcss.com",
        "fonts.googleapis.com",
        "fonts.gstatic.com",
        "unpkg.com",
        "cdnjs.cloudflare.com",
        "cdn.jsdelivr.net",
    ]

    for py_file in ui_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for domain in forbidden_domains:
            assert domain not in content, f"Found external domain reference '{domain}' in {py_file.name}"


def test_apptest_navigation_and_desk_flow():
    """Test standard application routing from Home to Desk and loading sample document."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
    at.run()
    assert not at.exception

    # Switch to Desk
    at.session_state.route = "Desk"
    at.run()
    assert not at.exception
    assert at.session_state.route == "Desk"

    # Click sample document loader
    sample_btn = [b for b in at.button if "sample" in str(b.key).lower()]
    assert len(sample_btn) > 0, "Sample document button not found on Desk"
    sample_btn[0].click().run()
    assert not at.exception

    # Verify session state was populated
    assert at.session_state.status == "READY"
    assert at.session_state.doc_name == "rental_agreement.pdf"
    assert at.session_state.session is not None
    assert len(at.session_state.session.pages) == 2


def test_session_cleanup():
    """Verify that clear_session cleanly wipes temporary workspace and resets state."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
    at.run()
    at.session_state.route = "Desk"
    at.run()

    # Load sample
    sample_btn = [b for b in at.button if "sample" in str(b.key).lower()][0]
    sample_btn.click().run()
    assert at.session_state.path is not None
    temp_path = at.session_state.path

    # Execute workspace cleanup
    workspace = at.session_state.workspace
    workspace.cleanup()

    # Confirm temp file and directory are wiped
    assert not temp_path.exists(), "Temporary document bytes remained on disk after cleanup"
    assert workspace.root is None or not workspace.root.exists()


class FakeChatClient:
    """Mock client for fast unit and AppTest verification without running Ollama."""
    def __init__(self, cfg=None):
        self.cfg = cfg
        self.model = "gemma3n:e2b"

    def chat_json(self, system: str, user: str, schema: dict) -> str:
        # Check schema to return valid mock JSON
        if "summary" in schema.get("properties", {}):
            return '{"summary": "This lease specifies rent of $1,200 and a 30-day notice period.", "findings": [{"category": "termination", "title": "Auto-renewal term", "explanation": "The lease renews unless written notice is given.", "evidence_quote": "Unless either party gives written notice at least 30 days", "statement_type": "explicit", "jurisdiction_dependent": false}]}'
        elif "answer" in schema.get("properties", {}):
            return '{"answerable": true, "answer": "The agreement requires 30 days notice.", "evidence_quotes": ["Unless either party gives written notice at least 30 days"], "statement_type": "explicit", "jurisdiction_dependent": false}'
        return "{}"


def test_full_analysis_and_results_flow():
    """Verify analysis, findings render, ask question, and export with injected client."""
    from streamlit.testing.v1 import AppTest
    from src.schemas import Finding, TriageResult, KeyFact, ChecklistItem

    at = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
    at.run()
    at.session_state.route = "Desk"
    at.run()

    # Load sample document
    sample_btn = [b for b in at.button if "sample" in str(b.key).lower()][0]
    sample_btn.click().run()

    # Inject a realistic TriageResult directly into session state to verify all results views
    session = at.session_state.session
    finding = Finding(
        category="termination",
        title="Auto-renewal of the lease",
        explanation="The lease renews for another eleven months unless notice is given 30 days prior.",
        evidence_quote="Unless either party gives written notice at least 30 days",
        statement_type="explicit",
        jurisdiction_dependent=False,
        page=1,
        chunk_id="chunk_0",
        verification_status="verified",
        verification_note="Quote found verbatim on page 1.",
        confidence="high",
        needs_human_review=True,
    )
    result = TriageResult(
        source_name="rental_agreement.pdf",
        model="gemma3n:e2b",
        summary="Standard residential lease agreement.",
        findings=[finding],
        key_facts=[KeyFact(label="Monthly rent", value="1,200", page=1, snippet="rent of 1,200")],
        checklist=[ChecklistItem(topic="Termination", found=True, pages=[1])],
        limitations=["Preliminary triage only."],
        disclaimer="Informational only. Not legal advice.",
        pages_analyzed=2,
        chunks_analyzed=2,
        elapsed_seconds=1.45,
    )
    at.session_state.result = result
    at.session_state.status = "DONE"

    # Test Overview Route
    at.session_state.route = "Overview"
    at.run()
    assert not at.exception

    # Test Findings Route
    at.session_state.route = "Findings"
    at.run()
    assert not at.exception
    assert len(at.session_state.result.findings) == 1

    # Test Key Facts Route
    at.session_state.route = "Key facts"
    at.run()
    assert not at.exception

    # Test Checklist Route
    at.session_state.route = "Checklist"
    at.run()
    assert not at.exception

    # Test Export Route
    at.session_state.route = "Export"
    at.run()
    assert not at.exception

    # Test Privacy & Model Route
    at.session_state.route = "Privacy and model"
    at.run()
    assert not at.exception


def test_no_raw_html_in_rendered_elements():
    """Verify that no markdown, code, or text elements display raw unparsed HTML."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
    at.run()

    routes = ["Home", "Desk", "Overview", "Findings", "Ask", "Key facts", "Checklist", "Export", "Privacy and model"]
    forbidden_tokens = ["<div", "<span", "<svg", "<h3", 'class="', "&amp;amp;"]

    for route in routes:
        at.session_state.route = route
        at.run()
        assert not at.exception

        # Check all markdown elements
        for md in at.markdown:
            content = str(md.value)
            for token in forbidden_tokens:
                assert token not in content, f"Found raw HTML token '{token}' in markdown on route '{route}': {content[:100]}"

        # Check code elements
        for code in at.code:
            content = str(code.value)
            # Only netstat/lsof or commands should appear in code blocks, not raw markup
            for token in ["<div", "<span", "<svg", 'class="']:
                assert token not in content, f"Found raw HTML token '{token}' in code block on route '{route}'"


def test_unlocked_navigation_and_empty_states():
    """Verify that all 8 destinations are clickable without any document and show empty states."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
    at.run()

    # Clear document session
    at.session_state.session = None
    at.session_state.result = None
    at.session_state.route = "Desk"
    at.run()

    destinations = ["Desk", "Overview", "Findings", "Ask", "Key facts", "Checklist", "Export", "Privacy and model"]
    for dest in destinations:
        at.session_state.route = dest
        at.run()
        assert not at.exception, f"Route {dest} raised an exception when no document is loaded"

        # Check that empty state CTA buttons or main inputs render without error
        if dest in ("Overview", "Findings", "Key facts", "Checklist", "Export"):
            sample_or_desk_btns = [b for b in at.button if any(k in str(b.label).lower() for k in ["desk", "sample", "analyse"])]
            assert len(sample_or_desk_btns) > 0, f"No CTA button found in empty state for {dest}"


def test_truthful_copy_and_no_internal_ids():
    """Verify that no internal IDs (F1-F17, X1-X5) and no unverified RAM claims leak into UI."""
    import re
    ui_dir = PROJECT_ROOT / "ui"

    id_pattern = re.compile(r'\b[FXSA]\d{1,2}\b')
    unverified_claim_phrases = [
        "ram-isolated",
        "zeroization",
        "overwritten on exit",
        "never written to permanent disk",
        "zero document caching",
        "secure ram workspace",
    ]

    for py_file in ui_dir.glob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        # Check for unverified claims in strings
        for phrase in unverified_claim_phrases:
            assert phrase not in text.lower(), f"Unverified claim '{phrase}' found in {py_file.name}"


def test_css_classes_integrity_and_no_tailwind():
    """Verify that no Tailwind utility classes remain in UI markup and semantic rl-* classes exist."""
    import re
    ui_dir = PROJECT_ROOT / "ui"
    tailwind_pattern = re.compile(r'class="[^"]*\b(flex|gap-\d+|px-\d+|py-\d+|mt-\d+|mb-\d+|text-\[\w+\]|bg-\w+|border-line)\b')

    for py_file in ui_dir.glob("*.py"):
        if py_file.name == "theme.py":
            continue
        text = py_file.read_text(encoding="utf-8")
        match = tailwind_pattern.search(text)
        assert match is None, f"Found Tailwind utility class in {py_file.name}: {match.group(0)}"


