"""Single source of truth for all user-facing strings, error mappings, and safety wording.

Strict safety constraints:
- No legal-certainty words ("illegal", "safe to sign", "enforceable", "valid", "risk-free", "high risk", "low risk").
- Verification means syntactic presence only ("Quote found in document").
- Disclaimers and professional escalation guidance must be consistent.
"""

from typing import NamedTuple


class ErrorMessage(NamedTuple):
    title: str
    message: str
    next_step: str
    command: str | None = None


# Persistent disclaimers
DISCLAIMER_SHORT = "Informational only. Not legal advice."
DISCLAIMER_FULL = (
    "This tool is for informational triage only and does not give legal advice. "
    "A quotation found in the document confirms only that the text appears in the source; "
    "it does not verify statutory interpretation or legal status. "
    "Take any clause that matters to a qualified lawyer or legal aid service in your jurisdiction."
)
ESCALATION_ADVICE = (
    "Please take this clause to a qualified lawyer or a legal aid service in your jurisdiction "
    "and ask them to confirm how it applies to you."
)

# App branding and headers
APP_NAME = "Redline"
APP_TAGLINE = "Private legal triage"
APP_SUBTITLE = "Understand a legal document without it leaving your computer."
AIRGAP_BADGE_TITLE = "Local only"
AIRGAP_BADGE_SUB = "Nothing leaves this computer"

# Home Page Copy
HOME_HERO_HEADLINE_PRE = "Your contracts"
HOME_HERO_HEADLINE_HIGHLIGHT = "stay on your computer."
HOME_HERO_HEADLINE_POST = "Understand them anyway."
HOME_HERO_SUBTEXT = (
    "Upload a lease, job offer or terms of service. Get a plain-language overview "
    "with every candidate finding tied directly to the exact page it came from."
)
HOME_CTA_PRIMARY = "Open my desk"
HOME_CTA_SECONDARY = "See how privacy works"
HOME_PRIVACY_CALLOUT = "Local only · No account · No cloud"

HOME_HOW_IT_WORKS = [
    {
        "step": "1",
        "title": "Drop in a PDF or TXT",
        "desc": "Your file is saved to a temporary private folder on this computer while you work, and deleted when you clear the session or close the app.",
    },
    {
        "step": "2",
        "title": "Read locally",
        "desc": "A small local language model runs entirely on this device via your loopback interface.",
    },
    {
        "step": "3",
        "title": "Review with sources",
        "desc": "Review candidate findings side-by-side with exact highlighted pages and citations.",
    },
]

HOME_WHAT_YOU_GET = [
    {
        "title": "Findings with sources",
        "desc": "Candidate obligations, termination clauses, and notice rules placed directly beside the original page.",
    },
    {
        "title": "Ask the document",
        "desc": "Ask plain questions with cited passages, or see clearly when the document does not address them.",
    },
    {
        "title": "Key facts & checklist",
        "desc": "Structured tables of amounts, notice periods, and standard clause presence checks.",
    },
]

HOME_HONEST_LIMITS_DOES = [
    "Quotes exact passages from the text",
    "Renders the original page beside every claim",
    "Flags items needing professional review",
    "Separates verified quotes from unverified claims",
]

HOME_HONEST_LIMITS_NEVER = [
    "Say a clause is lawful, binding, or compliant",
    "Replace advice from a qualified lawyer",
    "Send document text or metadata across the network",
    "Read scanned documents (text-based PDFs and TXT only)",
]

TESTED_ON_DOCUMENTS = [
    "Rental agreements",
    "Employment contracts",
    "Non-disclosure agreements",
    "Terms of service",
]

# Vault Page Copy
VAULT_TITLE_UNLOCK = "Unlock Redline"
VAULT_SUBTITLE_UNLOCK = "Your passphrase never leaves this computer."
VAULT_TITLE_SETRUN = "Set an app passphrase"
VAULT_SUBTITLE_SETRUN = "Lock this screen on your local computer. Files remain in a private temporary folder on this device."
VAULT_DESC_LOCAL_LOCK = (
    "This local app lock gates the screen on this computer and does not encrypt files on disk. "
    "No account, no cloud, and nothing to sign into."
)
VAULT_RESET_WARNING = (
    "Resetting removes the local passphrase and clears any currently loaded session. "
    "Your files on disk are untouched."
)

# Desk Page Copy
DESK_TITLE = "Put a document on the desk."
DESK_SUBTITLE = "Understand a legal document without it leaving your computer."
DROPZONE_PROMPT = "Drop a PDF or TXT here, or browse files"
DROPZONE_LIMIT = "Max file size: 50 MB. Text-based PDFs only. Scanned documents are not supported yet."
SAMPLE_BUTTON_LABEL = "Use sample document"
SAMPLE_DOC_FILENAME = "rental_agreement.pdf"
ANALYSE_BUTTON_LABEL = "Analyse document"
ANALYSE_DISABLED_NO_DOC = "Upload or select a document first."
ANALYSE_DISABLED_MODEL_NOT_READY = "Local model is not ready. See readiness instructions above."
SPARSE_PAGE_WARNING = "Some pages contain very little text. Results may be incomplete."

# Processing Stage Copy
PROCESSING_TITLE = "Reading your document"
PROCESSING_SUBTITLE = "Everything is running on this computer."
PROCESSING_PROGRESS_TICK = "Reading section {current} of {total}"
PROCESSING_ELAPSED = "Elapsed {elapsed}"
PROCESSING_ESTIMATE = "About {remaining} remaining"
PROCESSING_DISCLAIMER = "Findings will appear here after every quote has been checked."
CANCEL_BUTTON_LABEL = "Cancel"
PROCESSING_CANCELLED_TOAST = "Stopped. Your document is still loaded on the desk."

# Findings Screen
FINDINGS_TITLE = "Candidate findings"
FINDINGS_SUBTITLE = "Extracted clauses compared against the source document. A quote found does not imply statutory compliance."
GROUP_VERIFIED_TITLE = "Quote found in document"
GROUP_UNVERIFIED_TITLE = "Could not be verified"
GROUP_UNVERIFIED_EXPLANATION = (
    "These are candidate statements where the model's claimed quote could not be located verbatim "
    "in the source document. They are displayed for transparent auditing. Treat them with caution."
)
UNVERIFIED_QUOTE_LABEL = "Model's claimed quote"
VERIFIED_QUOTE_LABEL = "Quoted from the document"
VIEW_IN_DOCUMENT_LABEL = "View in document"
VIEW_WITHOUT_HIGHLIGHT_LABEL = "Open page without highlight"
HOW_CHECKED_LABEL = "How this was checked"
CONFIDENCE_TOOLTIP = "Derived from consistency checks, not from the model."
EMPTY_FINDINGS_TEXT = "No findings were produced for this document. That does not mean it has no issues."
EMPTY_FILTER_TEXT = "No findings match your current filter selections."

# Ask Screen
ASK_TITLE = "Ask the document"
ASK_INPUT_PLACEHOLDER = "What would you like to know about this document?"
ASK_BUTTON_LABEL = "Ask"
ASK_EXAMPLES = [
    "When can the agreement be terminated?",
    "What fees or penalties are mentioned?",
    "What notice period is required?",
    "What happens if either party defaults?",
]
ANSWER_SILENT_TITLE = "The document doesn't seem to address this."
ANSWER_SILENT_MESSAGE = "Nothing in the extracted text supports an answer, so none is given."
ANSWER_VERDICT_TITLE = "I can't say whether this is lawful or binding."
ANSWER_VERDICT_MESSAGE = "This tool cannot determine legal status. Here is only what the document text says:"
ANSWER_EMPTY_INPUT_MSG = "Please type a question."

# Key Facts & Checklist
KEY_FACTS_TITLE = "Key facts"
KEY_FACTS_SUBTITLE = "Amounts, dates, durations and percentages located in the text."
KEY_FACTS_EMPTY = "No amounts, dates or durations were found in the text."
CHECKLIST_TITLE = "Clause checklist"
CHECKLIST_SUBTITLE = "Not found means the extracted text has no matching wording. It is not a legal conclusion."
CHECKLIST_FOUND_GROUP = "Wording found"
CHECKLIST_NOT_FOUND_GROUP = "No matching wording found"

# Export Screen
EXPORT_TITLE = "Export your report"
EXPORT_SUBTITLE = "Review and save an offline Markdown summary of all triage findings."
EXPORT_DOWNLOAD_BTN = "Download Markdown report"
EXPORT_INSIDE_TITLE = "What's inside this report"
EXPORT_INSIDE_ITEMS = [
    "Candidate findings with cited verbatim quotes",
    "Key facts table (amounts, dates, durations)",
    "Clause checklist comparison",
    "Session questions and answers",
    "Limitations and persistent triage disclaimer",
]
EXPORT_CAVEAT = "A quote found in the document does not mean the reading is correct. The report explicitly states this."

# Privacy Page
PRIVACY_HERO_STATEMENT = "What leaves this device during processing: NOTHING."
PRIVACY_STATUS_TITLE = "Live device status"
PRIVACY_VERIFY_TITLE = "How to verify offline operation"
PRIVACY_VERIFY_STEPS = [
    {
        "step": "1",
        "title": "Turn Wi-Fi and Ethernet off",
        "desc": "Disconnect all physical and wireless connections to test true offline execution.",
    },
    {
        "step": "2",
        "title": "Run a sample document",
        "desc": "Load the rental agreement on the Desk and click 'Analyse document'.",
    },
    {
        "step": "3",
        "title": "Audit loopback network activity",
        "desc": "Inspect open connections to confirm traffic is strictly confined to 127.0.0.1:11434.",
    },
]
PRIVACY_MONITOR_CMD_WIN = 'netstat -ano | findstr "11434"'
PRIVACY_MONITOR_CMD_UNIX = "lsof -i :11434"

# Clear Session
CLEAR_SESSION_TITLE = "Clear and start over"
CLEAR_CONFIRM_PROMPT = "This deletes the document and every result from this session. It cannot be undone."
CLEAR_CONFIRM_BTN = "Delete everything"
CLEAR_CANCEL_BTN = "Cancel"
CLEAR_SUCCESS_TOAST = "Session cleared. Temporary files were deleted from this computer."

# Error mapping table (Maps from backend exceptions to human-friendly title, message, next step)
ERROR_MAPPINGS: dict[str, ErrorMessage] = {
    "UnsupportedFormat": ErrorMessage(
        title="This file type isn't supported.",
        message="Redline supports text-based PDF and plain text (.txt) documents.",
        next_step="Upload a PDF or TXT file.",
    ),
    "EncryptedDocument": ErrorMessage(
        title="This PDF is password protected.",
        message="Encrypted or password-gated PDFs cannot be read locally.",
        next_step="Remove the password and upload again.",
    ),
    "UnreadableDocument": ErrorMessage(
        title="This file couldn't be read.",
        message="The document was empty or contained corrupted data streams.",
        next_step="Try another copy or re-export the file.",
    ),
    "NoExtractableText": ErrorMessage(
        title="No readable text was found.",
        message="This document appears to be a scanned image. Local OCR is not supported yet.",
        next_step="Use a text-based PDF or TXT document.",
    ),
    "OllamaUnavailable": ErrorMessage(
        title="The local model isn't running.",
        message="Could not connect to Ollama on the loopback endpoint 127.0.0.1:11434.",
        next_step="Start the model server, then retry.",
        command="ollama serve",
    ),
    "ModelMissing": ErrorMessage(
        title="The model isn't installed.",
        message="The required local model was not found in your Ollama library.",
        next_step="Install the model with Ollama, then retry.",
        command="ollama pull gemma3n:e2b",
    ),
    "ModelTimeout": ErrorMessage(
        title="The model took too long.",
        message="The local model exceeded the inference deadline for this section.",
        next_step="Retry the analysis, or try a smaller document.",
    ),
    "InvalidModelOutput": ErrorMessage(
        title="The model's reply couldn't be used.",
        message="The local model returned unexpected formatting. Nothing was guessed or filled in.",
        next_step="Retry the request.",
    ),
    "EmptyQuestion": ErrorMessage(
        title="Please type a question.",
        message="A question is required to search the document.",
        next_step="Type a question into the search bar.",
    ),
    "PrivacyViolation": ErrorMessage(
        title="A network connection was blocked to protect your document.",
        message="An outbound network request outside loopback was intercepted and terminated.",
        next_step="Check your configuration; all triage processing is restricted to local execution.",
    ),
}

# Forbidden words list for safety audit (stand-alone whole-word checks)
FORBIDDEN_WORDS = [
    "illegal",
    "safe to sign",
    "enforceable",
    "valid",
    "risk-free",
    "high risk",
    "low risk",
]

import re

def audit_string_safety(text: str) -> list[str]:
    """Audit a string to ensure it does not contain prohibited legal certainty words."""
    found_violations: list[str] = []
    for word in FORBIDDEN_WORDS:
        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        if pattern.search(text):
            found_violations.append(word)
    return found_violations
