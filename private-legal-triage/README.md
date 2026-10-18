# Private Legal Document Triage Agent (PS2)

Local-first, privacy-preserving backend for preliminary legal document triage. Parses contracts (PDF and text), runs deterministic facts and checklist extraction, retrieves passages with BM25, and queries a local Google Gemma 3n model (via Ollama) to extract candidate legal findings and answer user questions. Every citation is verified against the source text before display.

> [!IMPORTANT]
> **Legal Disclaimer**: This tool provides a preliminary, informational reading of a document. It is not a lawyer, does not provide legal advice, and cannot determine whether any clause is valid or enforceable. Citation verification proves only that the text exists; it does not prove the model's interpretation is correct. Consult a qualified legal professional before making any consequential legal decision.

---

## Key Features

- **Local & Private**: Zero external network or API calls. Operates under `network_guard()` restricting all traffic strictly to `127.0.0.1:11434`.
- **Programmatic Citation Verification**: Quotes returned by the model are fuzzy/exact matched against source text and page boundaries.
- **Model Choice & Safety**: Manual selection between `gemma3n:e2b` and `gemma3n:e4b`. No automatic hidden model switching. Unloads prior models to keep memory footprint bounded (~2.4GB VRAM for E2B).
- **FastAPI & Python Direct API**: Seamlessly integrates with React/Vite web frontends (FastAPI) or Streamlit/Python apps (`DocumentSession`).
- **CUAD Evaluated**: Benchmark evaluated against the Atticus Project's CUAD dataset (40 contracts, 21 clause types, Top-5 recall >80%).

---

## Setup & Quickstart

Tested on Windows 11 and Linux with **Python 3.10 - 3.12**.

### 1. Environment & Dependencies

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # On Windows PowerShell: .venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
pip install -r requirements-api.txt    # For FastAPI REST server
pip install -r requirements-eval.txt   # For CUAD benchmarking
```

### 2. Pull Local Model & Run Connection Diagnostic

```bash
# Pull supported model
ollama pull gemma3n:e2b

# Verify connection and test live inference
python scripts/ollama_check.py
```

---

## Usage

### Command Line Interface (CLI)
```bash
python -m src.cli samples/rental_agreement.pdf --ask "How much notice does the tenant need?"
python -m src.cli samples/rental_agreement.pdf --json
```

### FastAPI REST Server
```bash
uvicorn src.api:app --host 127.0.0.1 --port 8000
```
Interactive docs at `http://127.0.0.1:8000/docs`.

### Direct Python / Streamlit API
```python
from src.pipeline import DocumentSession

session = DocumentSession("contract.pdf")
result = session.analyze(model="gemma3n:e2b")
answer = session.ask("What happens if I pay late?", model="gemma3n:e2b")
```

---

## Testing & Verification

### Unit Tests
```bash
python -m pytest -q
```
*127 passed, 9 skipped (unit test baseline without model dependency)*

### Ruff Linter
```bash
python -m ruff check .
```

### Privacy & Offline Audit
```bash
python scripts/privacy_check.py
```
*Verifies strict loopback socket isolation and zero log leakage.*

### Real Gemma 3n E2B Integration Tests (Opt-in)
```powershell
# Windows PowerShell
$env:TRIAGE_RUN_REAL_MODEL="1"; python -m pytest tests/integration/test_real_gemma.py -v

# Bash
TRIAGE_RUN_REAL_MODEL=1 python -m pytest tests/integration/test_real_gemma.py -v
```
*8 passed, 1 skipped (live local Gemma 3n E2B inference)*

### CUAD & Answer Evaluations
```bash
# BM25 CUAD clause retrieval benchmark
python eval/retrieval_eval.py --subset 40

# Grounded Q&A evaluations
python eval/answer_eval.py --retrieval-only
python eval/answer_eval.py --model gemma3n:e2b
```

---

## Detailed Documentation

- [Backend Technical Specification](file:///docs/backend.md)
- [Setup & Windows Installation Guide](file:///docs/SETUP.md)
- [Evaluation Methodology & CUAD Results](file:///docs/EVALUATION.md)
- [Privacy Architecture & Storage Threat Model](file:///docs/PRIVACY.md)
- [CUAD Retrieval Benchmark Report](file:///reports/cuad_retrieval_bm25.md)
- [Real Model Execution Results](file:///reports/real_model_run.json)
