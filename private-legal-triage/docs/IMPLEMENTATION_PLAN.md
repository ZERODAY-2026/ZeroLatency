# Antigravity Implementation Plan — Private Legal Document Triage Agent
## Priority-First Backend Fixes, CUAD Evaluation, and Local Ollama Verification

**Project:** Private Legal Document Triage Agent (Hackathon PS2)  
**Primary goal:** Make the existing backend reliably answer questions from private legal documents using a locally running Gemma 3n model through Ollama.

---

## Instructions for Antigravity

Work on the existing codebase. **Do not rewrite the project from scratch, replace working modules without evidence, or add unrelated features.** Inspect the current implementation before editing it. Preserve existing API contracts unless a change is necessary; if you change one, update the tests and documentation.

The backend archive contains these relevant modules:

- `src/api.py`
- `src/gemma_client.py`
- `src/models.py`
- `src/qa.py`
- `src/pipeline.py`
- `src/service.py`
- `src/privacy.py`
- `src/citation_validator.py`
- `src/document_parser.py`
- `eval/answer_eval.py`
- `eval/retrieval_eval.py`
- `eval/embedding_compare.py`
- `eval/cuad_setup.py`
- `tests/integration/test_real_gemma.py`
- `scripts/privacy_check.py`

Verify these paths against the actual workspace. Do not assume this list is exhaustive.

### Non-negotiable requirements

1. **Local inference only:** legal document contents, retrieved passages, prompts, and questions must not be sent to a cloud LLM or external service.
2. **Manual model selection:** the user explicitly selects `gemma3n:e2b` or `gemma3n:e4b`. Do not automatically switch models based on confidence or errors.
3. **Only the selected model should be loaded for inference.** When switching, unload the previously selected model when supported and verify actual residency. Do not claim this is guaranteed unless tested.
4. **Evidence-grounded answers:** answers must be supported by retrieved document passages, with page/section references where available.
5. **Citation validity is not answer correctness:** validate quotes, but separately test whether the answer correctly represents the cited evidence.
6. **Safe uncertainty:** when evidence is missing, ambiguous, contradictory, or insufficient, say so, abstain from unsupported conclusions, and recommend qualified legal advice where appropriate.
7. **Reproducible evaluation:** separate mocked/stub tests from tests using the real local Ollama model. Never present mock results as real-model results.
8. **No invented results:** run the checks and report their actual outputs. Do not mark a task complete because code was generated.
9. **Keep private data and datasets out of Git:** do not commit user documents, CUAD files, model weights, local databases, virtual environments, logs containing document contents, or secrets.
10. **Keep changes focused:** after each priority, run relevant tests and report changed files, commands run, results, and unresolved issues.

---

# Priority 0 — Verify the local Ollama connection first

Before changing inference code, establish whether the machine running the backend can reach the user's local Ollama instance. Do not assume that a successful mock test proves connectivity.

## 0.1 Inspect the current implementation

Inspect `src/gemma_client.py`, `src/models.py`, `src/config.py`, `src/api.py`, and `.env.example` (if present).

Verify:

- The configured Ollama base URL defaults to `http://127.0.0.1:11434`.
- Requests go only to the configured loopback endpoint; reject non-loopback hosts.
- The model name is checked against an explicit allowlist.
- The requested model is passed through the complete API/service/pipeline path, not silently replaced by a default.
- Missing Ollama service, missing model, timeout, malformed JSON, and out-of-memory cases produce clear errors.
- No cloud provider SDK or external inference endpoint is used by the question-answering path.
- HTTP client configuration does not inherit proxy environment variables for the local Ollama call; use a safe local-only configuration.
- Model selection is explicit and no confidence-triggered automatic fallback exists.

## 0.2 Add or verify a connection diagnostic

Provide a diagnostic command or script that:

1. Calls `GET http://127.0.0.1:11434/api/tags`.
2. Reports whether Ollama is reachable.
3. Lists installed model names returned by Ollama.
4. Checks whether the selected model is installed.
5. Makes a small, non-sensitive test inference using the selected model.
6. Reports success/failure, duration, and a concise error without exposing document contents or secrets.
7. Does not automatically download a model or switch models.

Use the Ollama API documented by the installed version. Do not fake a successful response.

If Ollama is not reachable, give the exact next step instead of reporting success.

## 0.3 Manual Windows verification for the user

The developer should document these commands in the setup guide. The user can run them in **PowerShell on the same Windows laptop that runs the backend**:

```powershell
ollama --version
ollama list
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

Confirm the exact model identifier shown by `ollama list`. If the selected model is missing, tell the user to pull that exact supported model using Ollama. Do not assume it is installed.

Then test a real local inference:

```powershell
ollama run gemma3n:e2b "Reply with exactly: LOCAL_MODEL_OK"
```

If the installed model identifier differs, use the exact identifier reported by `ollama list`, provided it is supported by the application's allowlist.

Run the backend's diagnostic command from the same machine and Python environment used to launch FastAPI. A connection test run in another computer, container, or cloud environment does **not** verify connectivity to Ollama on the user's laptop.

## 0.4 Report the connection state accurately

Report one of these states:

- `PASS — LOCAL OLLAMA REACHABLE AND SELECTED MODEL INFERRED`
- `PARTIAL — OLLAMA REACHABLE, SELECTED MODEL MISSING`
- `FAIL — OLLAMA NOT REACHABLE`
- `NOT VERIFIED — test could not be run on the user's laptop`

Do not claim the user's laptop connection is verified unless the test actually ran there.

**Acceptance criteria**

- A real, non-mocked request reaches local Ollama.
- The response comes from the selected model.
- Missing service/model errors are clear.
- No external inference URL is contacted.
- Test logs contain no private document text.

---

# Priority 1 — Fix real-model question-answering correctness

This is the highest functional priority. The previous review identified a recorded real-model case where a synthetic employment-contract question expected a 45-day notice period but the result was marked `answerable: false`. Reproduce the case before changing code; do not assume the failure's cause.

## Tasks

1. Inspect `src/qa.py`, the question-answering prompt, response schemas, retrieval result format, and `tests/integration/test_real_gemma.py`.
2. Reproduce the 45-day notice-period test using the actual local Gemma model.
3. Determine whether the failure comes from:
   - BM25 not retrieving the correct passage;
   - the correct passage being retrieved but omitted from the model prompt;
   - prompt wording or context truncation;
   - JSON/schema parsing;
   - answerability/abstention logic;
   - citation validation;
   - an incorrect test expectation or fixture.
4. Fix the identified root cause rather than hardcoding the expected answer.
5. Add assertion-based tests for:
   - an answer explicitly present in the document;
   - paraphrased wording;
   - information absent from the document;
   - two passages needed to answer;
   - conflicting provisions;
   - dates, durations, amounts, parties, termination, penalties, and governing law;
   - malformed model output;
   - a quotation that exists but does not support the answer.
6. Use a structured answer schema with at least:
   - `answer`
   - `answerable` or an explicit abstention status
   - `evidence` containing quote and page/section references
   - `uncertainty` / limitations
   - `reason` for abstention where applicable.
7. Validate each evidence quote against the original extracted page text. Distinguish `quote_verified` from `claim_supported`; do not label a whole answer correct just because a quote matches.
8. If the source does not support an answer, return an explicit insufficient-evidence response rather than guessing.
9. Add regression tests for every fixed failure.

**Acceptance criteria**

- The 45-day test passes for the right reason and cites the correct source passage.
- Unanswerable questions abstain reliably.
- A valid quotation that does not entail the answer does not make the answer pass.
- Mock tests and real-model tests are separately labeled.
- No expected answer is hardcoded into production code.

---

# Priority 2 — Enforce and verify privacy across the actual FastAPI path

The previous review found that the privacy guard was exercised in CLI/audit paths, but the FastAPI request path was not visibly shown to wrap all relevant processing in the guard. Confirm this against the current code and fix the actual gap.

## Tasks

1. Trace the complete FastAPI lifecycle from upload through parsing, indexing, `/ask`, `/analyze`, result retrieval, cancellation, and deletion.
2. Confirm every LLM request uses the local Ollama client and that no external AI API is used.
3. Add a defense-in-depth privacy design:
   - enforce loopback-only model endpoints;
   - reject unexpected external inference endpoints;
   - disable proxy inheritance for local Ollama requests;
   - avoid third-party telemetry and external analytics;
   - avoid logging document text, prompts, or sensitive answers;
   - keep temporary documents, indexes, and result storage local;
   - remove temporary artifacts on deletion and error paths where intended.
4. Ensure the privacy protection is applied consistently to the actual API execution path, not just a CLI command or test harness.
5. Do not rely on monkey-patching Python sockets as the sole security boundary. Clearly document that native libraries, subprocesses, and other processes may bypass such a guard. Recommend OS-level outbound network restrictions for strong offline enforcement.
6. Add tests that attempt external HTTP and DNS access in a controlled test environment and verify that attempted access is blocked or fails closed as designed.
7. Add a manual privacy verification guide for the user:
   - download model/dependencies first;
   - disable internet access;
   - start Ollama and FastAPI locally;
   - upload and analyze a test contract;
   - inspect active network connections and firewall/network-monitor output;
   - verify the app still works offline;
   - check logs and temporary directories for leaked text.
8. Never claim the entire application is private solely because Ollama uses `127.0.0.1`. State exactly what was tested and what remains dependent on OS configuration.
9. Test deletion behavior. Do not claim secure physical erasure on SSDs or journaling filesystems.

**Acceptance criteria**

- FastAPI paths use only the local model endpoint.
- Privacy tests cover the real API service layer and are not limited to mocks.
- Offline operation is demonstrated on the user's machine.
- The documentation distinguishes application-level controls from OS-level enforcement.
- No document content or secrets appear in logs.

---

# Priority 3 — Improve retrieval and benchmark alternatives using CUAD

CUAD is an evaluation dataset, not a required runtime dependency and not something that must be uploaded to Gemma. Use it locally to evaluate clause retrieval and evidence grounding.

## Tasks

1. Locate the CUAD dataset the user has already added to the project. Do not download a second copy or move/delete the user's data without asking.
2. Inspect the dataset format and license/attribution notes. Keep it out of Git unless the repository explicitly and lawfully intends to redistribute it.
3. Inspect `eval/cuad_setup.py` and `eval/retrieval_eval.py`; reuse and fix these scripts rather than duplicating them.
4. Make dataset paths configurable through CLI arguments or configuration, not hardcoded absolute paths.
5. Build or verify a reproducible subset evaluation. Record the subset selection and random seed if sampling.
6. Measure at least:
   - Recall@1, Recall@3, and Recall@5;
   - reciprocal rank / MRR if suitable labels are available;
   - no-relevant-passage cases;
   - latency.
7. Compare current BM25 with the existing embedding-based comparison in `eval/embedding_compare.py`, if the embedding implementation is truly local and reproducible.
8. Do not replace BM25 merely because embeddings sound better. Compare actual metrics, privacy implications, dependencies, memory, and latency.
9. Verify that retrieval output preserves source document ID, page number, chunk ID, and exact source text.
10. Add manually reviewed rental and employment agreement cases because CUAD's commercial contracts do not fully represent those document types.

**Acceptance criteria**

- CUAD evaluation runs using the user's local dataset path.
- Dataset loading errors are actionable.
- Metrics are computed from actual predictions and labels, not invented values.
- BM25 and any alternative are compared on the same fixed evaluation subset.
- The dataset is not needed for normal runtime inference.

---

# Priority 4 — Evaluate full answers, not retrieval alone

## Tasks

1. Inspect `eval/answer_eval.py` and `eval/cases/synthetic_cases.json`.
2. Separate:
   - retrieval-only evaluation;
   - mocked-model evaluation;
   - real Ollama/Gemma evaluation.
3. Build a small, independently reviewed answer test set with known supporting passages and expected facts.
4. Report:
   - factual answer correctness;
   - citation quote validity;
   - citation support for the associated claim;
   - unsupported-claim rate;
   - correct abstention rate;
   - false abstention rate;
   - structured-output validity;
   - latency and memory usage.
5. Ensure tests compare semantic/factual outcomes appropriately instead of relying only on exact string matches.
6. Save machine-readable results (JSON/CSV) and a concise Markdown report. Do not put sensitive user documents in results.
7. Record model identifier, Ollama version, configuration, test-set version, date, and whether inference was real or mocked.
8. Treat the report's previous CUAD Recall@5 result of about 80.2% as a historical baseline only; rerun the current evaluation before presenting it as current.

**Acceptance criteria**

- A single command can run the documented evaluation subset.
- Real-model results cannot silently be replaced by mock results.
- Every reported metric is traceable to generated outputs and labeled test data.
- Failure examples are summarized without exposing private documents.

---

# Priority 5 — Model lifecycle, failure handling, and API consistency

## Tasks

1. Trace the selected model through API → service → pipeline → `gemma_client.py`.
2. Verify E2B/E4B manual selection works end to end.
3. Test switching models, unloading the prior model when supported, and checking actual residency through Ollama.
4. Never automatically switch to another model when the selected model fails.
5. Test:
   - Ollama stopped/unavailable;
   - model not installed;
   - unsupported model identifier;
   - request timeout;
   - invalid JSON;
   - context/memory exhaustion;
   - concurrent analysis requests;
   - cancellation during inference;
   - document deletion during or after a job.
6. Keep error messages useful but avoid including private text or secrets.
7. Review API response models and status codes for consistency with actual behavior.
8. Ensure the document is parsed/indexed once per session where possible; model switching should not needlessly reparse the document.
9. Add or update tests for all fixed regressions.

**Acceptance criteria**

- API model selection matches the user's explicit choice.
- Unsupported or missing models produce clear errors.
- No silent fallback occurs.
- Cancellation and cleanup behave predictably.
- Existing API routes remain compatible or are documented if changed.

---

# Priority 6 — Document extraction and robustness

OCR is not required for the first working version, but limitations must be explicit.

## Tasks

1. Test PDFs with searchable text, scanned pages, mixed pages, malformed files, encryption, unusual page sizes, and empty text.
2. If OCR is implemented, use a local OCR engine and do not send pages to an external OCR API. Otherwise, reject/report pages without extractable text clearly.
3. Test the documented size/page limits and very long contracts.
4. Confirm page references remain accurate after chunking and retrieval.
5. Handle Unicode, line breaks, hyphenation, tables, and clause boundaries without silently fabricating source text.
6. Make extraction coverage visible to the user: which pages were processed, skipped, or could not be read.

**Acceptance criteria**

- The backend never claims to analyze text it did not extract.
- Scanned or unreadable pages are clearly identified.
- Citations retain the correct original page numbers.
- Limits fail with clear errors instead of crashing.

---

# Priority 7 — Repository hygiene, tests, and reproducible setup

## Tasks

1. Update `.gitignore` to exclude:
   - `.venv/`, `.venv*/`, `venv/`, `env/`;
   - `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`;
   - local document uploads, private workspaces, local indexes/databases;
   - CUAD datasets and generated evaluation artifacts where appropriate;
   - model weights and environment secrets.
2. Inspect Git tracking status. If a virtual environment or private data is already tracked, explain how to remove it from tracking without deleting the user's local copy.
3. Do not commit `.env`, credentials, private legal documents, downloaded datasets, or model weights.
4. Run:
   - `python -m pytest -q`;
   - `python -m ruff check .` if Ruff is installed;
   - the privacy audit;
   - local Ollama smoke test;
   - real-model integration tests when the model is installed and available;
   - CUAD retrieval evaluation;
   - answer-quality evaluation.
5. Clearly label tests skipped because they require Ollama, model downloads, or large datasets.
6. Update README/setup instructions for Windows PowerShell, including Python environment setup, Ollama verification, model selection, API launch, and test commands.
7. Provide a final report with:
   - files changed;
   - bugs found and fixed;
   - exact commands executed;
   - actual pass/fail/skip counts;
   - real-model connection status;
   - evaluation metrics;
   - privacy tests actually performed;
   - remaining limitations.

**Acceptance criteria**

- Fresh setup instructions are reproducible.
- No private data, secrets, virtual environments, or model weights are accidentally staged.
- Tests are actually run, and results are not fabricated.
- Documentation matches current behavior.

---

# Required final report from Antigravity

When implementation is complete, respond with this structure:

1. **Local Ollama connection:** PASS / PARTIAL / FAIL / NOT VERIFIED, with exact command and actual output summary.
2. **Selected model:** exact model identifier reported by Ollama; do not guess.
3. **Changes made:** files and reasons.
4. **Tests:** actual pass/fail/skip counts and commands.
5. **CUAD evaluation:** dataset path, subset size, metrics, and any data limitations.
6. **Real-model QA:** results for the 45-day notice case and other answer tests.
7. **Privacy:** tests performed, evidence, and what remains unverified.
8. **Known limitations:** no unsupported claims of completion.
9. **Next actions for the user:** only steps that genuinely require user action.

Do not state that Ollama is connected on the user's laptop unless a real connection test has run on that laptop. Do not state that privacy is proven unless the stated privacy tests were actually performed.
