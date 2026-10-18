# Frontend Specification: Private Legal Document Triage Agent (PS2)

## 1. Purpose and mental model

The frontend is a Streamlit app that sits on top of the finished backend. It is a reading desk, not a verdict machine. The user puts a document on the desk, the app shows what it found with the source page open beside each finding, and it is always clear which statements are quoted from the document, which are possible readings, and which could not be checked.

The UI contains no document-processing logic. Every result comes from `DocumentSession`, and nothing is shown as verified unless `verification_status == "verified"`.

## 2. Principles

- **Evidence beside every claim:** each finding is one click from the highlighted source page.
- **Uncertainty is a first-class element:** it uses words and icons, never colour alone.
- **No legal-certainty signals:** no green "safe", "legal" or "OK" markers. A verified badge means "quote found in the document", nothing more.
- **Plain language:** short sentences, no unexplained jargon, a glossary-style tooltip for terms where useful.
- **Privacy is visible:** the user can always see where processing happens and what, if anything, left the device.
- **Fail clearly:** every error has a human message and a next step, and never includes document text.
- **Local only:** Streamlit is bound to loopback with usage statistics off.

## 3. Run configuration

`.streamlit/config.toml` (committed; secrets stay ignored):

```toml
[server]
address = "127.0.0.1"
headless = true
maxUploadSize = 50
enableCORS = false

[browser]
gatherUsageStats = false
serverAddress = "127.0.0.1"

[client]
toolbarMode = "minimal"
```

Run: `streamlit run app.py`. Streamlit sends usage statistics by default, so `gatherUsageStats = false` is mandatory for the privacy claim.

## 4. Feature list

### Core (maps to guide requirements L1 to L10)

| ID | Feature | Backend call |
|---|---|---|
| F1 | Upload a PDF or TXT, with type and size validation | `PrivateWorkspace.save_upload`, `DocumentSession(...)` |
| F2 | Document readiness check (pages, text found, sparse-page warning) | `session.pages`, `low_text_pages` |
| F3 | Analysis with live progress and elapsed time | `session.analyze(on_progress)` |
| F4 | Plain-language summary | `result.summary` |
| F5 | Candidate findings list with filters and sorting | `result.findings` |
| F6 | Finding cards: category, statement type, verification, confidence, review and jurisdiction flags | `Finding` fields |
| F7 | Source viewer: PDF page image with quote highlighted; text view for TXT | `highlight.render_page` |
| F8 | Unverified findings separated and clearly labelled | `verification_status` |
| F9 | Ask a question about the document, with cited answer | `session.ask` |
| F10 | "Document is silent" and "verdict declined" answer states with escalation advice | `Answer` fields |
| F11 | Key facts table (amounts, dates, durations, percentages) | `result.key_facts` |
| F12 | Clause checklist (found or no matching wording) | `result.checklist` |
| F13 | Limitations panel | `result.limitations` |
| F14 | Privacy and model panel with network-guard status | `network_guard`, settings |
| F15 | Export Markdown report | `report.to_markdown` |
| F16 | Clear session: wipe temp files and in-memory state | `PrivateWorkspace.cleanup` |
| F17 | Persistent disclaimer and escalation guidance | `DISCLAIMER`, `ESCALATION` |

### Recommended extras

| ID | Feature |
|---|---|
| X1 | Jump from a key fact or checklist hit to its page in the source viewer |
| X2 | Example questions to start the Q&A |
| X3 | "Needs professional review" shortlist: only findings with `needs_human_review` |
| X4 | Benchmark card: pages, chunks, model, elapsed seconds, and (manually entered) memory use |
| X5 | Prompt-injection notice when the document contains instruction-like text |

## 5. Screens and navigation

One Streamlit app with a persistent sidebar and a state-driven main area (no page reloads between steps).

```text
Sidebar (always)                     Main area
+-------------------------+          +---------------------------------------------+
| Private Legal Triage    |          |  Screen depends on state:                   |
| [Local only] badge      |          |   S1 Upload -> S2 Processing -> S3 Results  |
| Document: name, pages   |          |   S4 Privacy & model (any time)             |
| Model: gemma3n:e2b      |          |   S5 Error (inline, any step)               |
| [Privacy & model]       |          +---------------------------------------------+
| [Clear and start over]  |
| Disclaimer (short)      |
+-------------------------+
```

### S1: Upload

Purpose: get a valid document in and confirm the system is ready.

Layout:
- Title and one-sentence promise: "Understand a legal document without it leaving your computer."
- Readiness banner from `OllamaClient.check_ready()`: green text "Local model ready", or a warning with the fix (`ollama serve`, `ollama pull gemma3n:e2b`). Analysis stays disabled until ready.
- File uploader (PDF, TXT). Helper text: "Text-based PDFs only. Scanned documents are not supported yet."
- Scope note: states the document categories the tool was tested on.
- "Use sample document" button that loads `samples/rental_agreement.pdf` for demos.
- On a successful parse, a document card: file name, page count, characters extracted, pages with little text, and a button **Analyse document**.

### S2: Processing

- Progress bar and text "Reading section 3 of 12", driven by `on_progress`.
- Elapsed time and an estimate after the first section completes.
- Reminder line: "Everything is running on this computer."
- **Cancel** button. Streamlit reruns on widget interaction and stops the running script, so cancelling returns to the document card and keeps the file loaded.
- No partial findings are shown until validation has finished.

### S3: Results workspace

Header strip: document name, counts (findings, verified, needing review), elapsed time, and the short disclaimer. Below it, five tabs.

**T1 Overview**
- Summary card with label "Preliminary overview".
- Counts by category.
- Top "needs professional review" items (X3), each linking to its finding.
- Prompt-injection notice if present (X5).
- Limitations expander, open by default (F13).

**T2 Findings**
- Filter bar: category, statement type, verification, confidence, "needs review only", free-text search over title and explanation.
- Sort: page order (default) or review priority.
- Two groups: **Quote found in document**, and **Could not be verified** (collapsed, with an explanation of why these are shown at all).
- Finding card (section 6) on the left, source viewer on the right (stacked on narrow screens).

**T3 Ask**
- Text input and example prompts (X2).
- Answer cards stacked newest first, kept for the session.
- Answer states (section 7).

**T4 Key facts and checklist**
- Key facts table with columns label, value, page, snippet, and a "View page" action (X1).
- Checklist list grouped as "Wording found" and "No matching wording found", with pages. Caption: "Not found means the extracted text has no matching wording. It is not a legal conclusion."

**T5 Export**
- Download Markdown report (includes findings, key facts, checklist, asked questions, limitations, disclaimer).
- Short explanation of what is in the file.

### S4: Privacy and model

Always reachable from the sidebar.
- Where processing happens: model endpoint `127.0.0.1:11434`, network guard active, blocked-attempt counter for this session (host names only).
- "What leaves this device during processing: nothing."
- Network calls table: setup versus processing (same table as `architecture.md`).
- How to verify: steps to turn Wi-Fi off and run the sample, and the connection-monitoring command to use.
- Threat model summary and what is out of scope.
- Model identity, quantization, runtime, licence and attribution, with a link to the model terms.
- Benchmark card (X4).

### S5: Error screen

Inline error card with a title, one plain sentence, and a next step. Mapping:

| Backend error | Message | Next step |
|---|---|---|
| `UnsupportedFormat` | "This file type isn't supported." | Upload a PDF or TXT. |
| `EncryptedDocument` | "This PDF is password protected." | Remove the password and upload again. |
| `UnreadableDocument` | "This file couldn't be read." | Try another copy or export it again. |
| `NoExtractableText` | "No readable text was found. This may be a scanned document." | Use a text-based PDF. OCR isn't supported yet. |
| `OllamaUnavailable` | "The local model isn't running." | Start it with `ollama serve`, then retry. |
| `ModelMissing` | "The model isn't installed." | Run `ollama pull gemma3n:e2b`. |
| `ModelTimeout` | "The model took too long." | Retry, or use a smaller document. |
| `InvalidModelOutput` | "The model's reply couldn't be used." | Retry. Nothing was guessed or filled in. |
| `EmptyQuestion` | "Please type a question." | None. |
| `PrivacyViolation` | "A network connection was blocked to protect your document." | Report this; it should not happen. |

## 6. Finding card

```text
+----------------------------------------------------------------------+
| Auto-renewal of the lease                          Page 1            |
| [Obligation] [Stated in document] [Quote found] [Confidence: high]   |
| [Review with a professional] [Depends on local law]   (when set)     |
|                                                                      |
| The lease renews for another eleven months unless you give notice    |
| at least 30 days before it ends.                                     |
|                                                                      |
| > "Unless either party gives written notice at least 30 days ..."    |
|                                                                      |
| [View in document]   [How this was checked v]                        |
+----------------------------------------------------------------------+
```

Badge wording (text always present, colour is secondary):

| Field | Display |
|---|---|
| `statement_type = explicit` | "Stated in document" |
| `statement_type = interpretation` | "Possible reading" |
| `verification_status = verified` | "Quote found in document" |
| `verification_status = unverified` | "Could not verify quote" (warning icon) |
| `confidence` | "Confidence: low, medium or high", with tooltip "Derived from checks, not from the model" |
| `needs_human_review` | "Review with a professional" |
| `jurisdiction_dependent` | "Depends on local law" |

Behaviour:
- **How this was checked** expands `verification_note` and any `ungrounded_figures` ("These figures do not appear in the document: 40000").
- Unverified cards use a neutral warning style, show the quote as "Model's claimed quote", and have no "View in document" highlight (the page view still opens without a highlight).
- Corrected pages show "Page corrected from X to Y" from the note.

### Source viewer

- PDF: `render_page(path, page, quote)` PNG with the highlight, caption "Page N, highlighted passage", and previous or next page buttons.
- TXT: the page text with the quote wrapped in a highlight, found with a whitespace-tolerant search.
- If the highlight cannot be located on the page, show the page without it and say "The passage was verified but could not be highlighted."
- Image alt text: "Page N of the document with the cited passage highlighted".

## 7. Answer states (Ask tab)

| State | Condition | Presentation |
|---|---|---|
| Answered | `answerable` | Answer text, "Stated in document" or "Possible reading" label, evidence quotes with page and a "View in document" action, escalation note if `jurisdiction_dependent` |
| Silent | not `answerable` | Neutral card: "The document doesn't seem to address this." Not styled as an error. Escalation line shown. |
| Verdict declined | `verdict_declined` | Card headed "I can't say whether this is legal or enforceable", then only what the text says, then escalation advice |
| Unverified evidence | some evidence `unverified` | Those quotes shown with a warning label and excluded from "View in document" |

## 8. Workflow

### State machine

```text
IDLE --upload ok--> READY --Analyse--> ANALYZING --done--> DONE
  ^                   |                    |                 |
  |                   +--parse error-->  ERROR <--model error+
  +-------------- Clear and start over (from any state) ----+
```

Session keys: `status`, `workspace`, `path`, `session` (the `DocumentSession`), `result`, `answers`, `selected_finding`, `viewer_page`, `blocked_hosts`, `error`, `ready_checked`.

### Step by step

1. **Startup:** run `check_ready()` once per session and show the result on S1.
2. **Upload:** open a `PrivateWorkspace`, save the upload under a random name, and call `DocumentSession(path)` inside `network_guard()`. A `DocumentError` goes to S5 with its mapped message. Success goes to READY with the document card.
3. **Analyse:** set ANALYZING and call `session.analyze(on_progress)` inside `network_guard()`. The callback updates the progress bar. On success the result is stored and the app moves to DONE and S3. A model error goes to ERROR with a Retry action that keeps the loaded document.
4. **Review:** the user filters findings, opens source pages, and reads limitations. Selecting "View in document" stores `selected_finding` and `viewer_page`, which only changes the viewer.
5. **Ask:** each question calls `session.ask(...)` inside `network_guard()`. The answer is appended to `answers`. `EmptyQuestion` is shown inline.
6. **Export:** build `to_markdown(result, answers)` on demand and offer it as a download.
7. **Clear and start over:** call `workspace.cleanup()`, empty `st.session_state`, and return to S1. This also runs when the user uploads a different file.

Rules:
- Uploaded bytes are never written outside the `PrivateWorkspace`.
- Backend calls that touch the document always run inside `network_guard()`, and any blocked hosts are appended to `blocked_hosts` for S4.
- The UI never caches document content to disk. In-memory state ends with the session.
- `DocumentSession` takes an injected client, so tests can substitute a fake. The shipped app has no mock mode, because the demo must show the real system.

## 9. Proposed file structure

```text
app.py                    entry point: config, sidebar, state-driven routing
ui/
├── __init__.py
├── state.py              session keys, status transitions, reset
├── sidebar.py            badge, document card, navigation, clear button
├── upload.py             S1
├── processing.py         S2
├── results.py            S3 header and tab wiring
├── overview.py           T1
├── findings.py           T2 list, filters, cards
├── ask.py                T3
├── facts.py              T4
├── export.py             T5
├── privacy_page.py       S4
├── source_view.py        PDF image and TXT highlight viewer
├── components.py         badges, answer card, error card
└── text.py               all user-facing strings and error mapping
```

All wording lives in `ui/text.py` so tone and disclaimers stay consistent and are easy to review.

## 10. Accessibility and usability

- Every status uses text plus an icon; colour never carries meaning alone.
- Logical heading order, with one `h1` per screen.
- Sufficient contrast in both Streamlit light and dark themes; no custom colours that fail contrast.
- Everything reachable by keyboard. Expanders and tabs use native Streamlit widgets.
- Page images have meaningful captions and alt text.
- Reading level aimed at a non-lawyer. Legal terms get a one-line plain explanation on first use.
- Long operations always show progress and a way out.
- Empty states are explicit: "No findings were produced for this document. That does not mean it has no issues."

## 11. Content and tone rules

- Say "candidate findings", "possible concern" and "preliminary overview".
- Never say "illegal", "safe to sign", "enforceable", "valid" or "risk-free" as the tool's own judgement.
- "Quote found in document" never implies the interpretation is right. The Overview and Export both repeat that.
- Disclaimer appears in the sidebar, the results header strip and the export. Escalation advice is specific: take the clause to a lawyer or legal aid service in your jurisdiction.

## 12. Testing

- Streamlit `AppTest` flows with an injected fake client: upload, analyse, filter, open the viewer, ask a question, silent answer, verdict-declined answer, export, clear session.
- Error-path tests: encrypted PDF, blank PDF, unsupported type, Ollama unavailable, model missing, invalid model output.
- State tests: clearing removes the workspace directory and empties session state.
- Text tests: no UI string contains forbidden certainty words.
- Manual: full run with Wi-Fi off and connection monitoring on, screen-recorded for the submission; keyboard-only pass; dark and light theme pass.

## 13. Build order

1. Skeleton: `app.py`, state machine, sidebar, upload, document card (S1).
2. Analysis with progress (S2) and error mapping (S5).
3. Overview and Findings with cards and badges.
4. Source viewer with highlighting.
5. Ask tab with all four answer states.
6. Key facts and checklist, Export, Privacy page.
7. Accessibility and wording pass, `AppTest` suite, demo recording.

## 14. Acceptance criteria

- A user can upload, analyse, review findings beside highlighted source pages, ask questions and export a report without leaving the app.
- Verified and unverified findings are visibly different, and the difference is readable without colour.
- Silent and verdict questions are handled as designed.
- Every error in section 5 shows its mapped message and next step, with no document text.
- Clearing the session removes temp files and in-memory state.
- The privacy page reflects real runtime state, and the full flow works offline.
- The disclaimer and escalation advice are always visible or one click away.

## 15. Known limitations

- Streamlit reruns on interaction, so cancelling stops the run but gives no partial results.
- TXT highlighting is text-based and less precise than PDF highlighting.
- Analysis is sequential, so long documents take a while. Progress and elapsed time are the mitigation.
- No multi-document comparison, OCR, or language selection in this version.
