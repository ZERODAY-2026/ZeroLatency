# Setup and Verification Guide

## System Requirements

- **Operating System**: Windows 10/11 (64-bit) or Linux (Ubuntu 22.04+)
- **Python**: Python 3.10 to 3.12 (Tested on Python 3.10.11 and Python 3.12.10)
- **Local Model Runtime**: Ollama (v0.40.6 or later)
- **Hardware**:
  - Minimum: 16 GB System RAM, modern multi-core x86_64 CPU
  - Recommended: NVIDIA GPU with at least 6 GB VRAM (e.g., RTX 3050 Laptop GPU / RTX 4060)

---

## 1. Environment Setup

### Windows (PowerShell)
```powershell
# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install base dependencies
pip install -r requirements.txt

# Install API dependencies (if using FastAPI/uvicorn)
pip install -r requirements-api.txt

# Install evaluation dependencies (for CUAD retrieval benchmarking)
pip install -r requirements-eval.txt
```

### Linux (Bash)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-api.txt
pip install -r requirements-eval.txt
```

---

## 2. Model Installation & Connection Diagnostic (Ollama)

Ensure Ollama is installed and running:
```bash
ollama serve
```

Pull the supported local models:
```bash
# Primary model (recommended: ~2.4GB VRAM footprint)
ollama pull gemma3n:e2b

# Optional larger model
ollama pull gemma3n:e4b
```

Verify installed models:
```bash
ollama list
```

### Run Ollama Local Connectivity Diagnostic
Verify loopback connectivity and live model inference using the diagnostic script:
```powershell
python scripts/ollama_check.py
# or
python -m scripts.ollama_check --model gemma3n:e2b
```
Expected output:
```
============================================================
OLLAMA LOCAL CONNECTION DIAGNOSTIC
============================================================
Target Loopback URL : http://127.0.0.1:11434
Target Model        : gemma3n:e2b
------------------------------------------------------------
[1/3] Checking Ollama service reachability... PASS (v0.40.6)
[2/3] Checking installed models... PASS (1 installed: gemma3n:e2b)
[3/3] Testing inference with 'gemma3n:e2b'... PASS (0.62s)
------------------------------------------------------------
[RESULT] PASS - LOCAL OLLAMA REACHABLE AND SELECTED MODEL INFERRED
============================================================
```

---

## 3. Running the Application

### Command Line Interface (CLI)
Run document triage under strict loopback isolation:
```powershell
python -m src.cli samples/rental_agreement.pdf
```

Ask a specific question against a contract:
```powershell
python -m src.cli samples/employment_contract.txt --ask "What is the notice period for resignation?"
```

Output as structured JSON:
```powershell
python -m src.cli samples/rental_agreement.pdf --json
```

### FastAPI REST API
Start the local FastAPI server:
```powershell
uvicorn src.api:app --host 127.0.0.1 --port 8000
```
Interactive OpenAPI documentation will be accessible at: `http://127.0.0.1:8000/docs`

---

## 4. Running Verification & Tests

### Fast Unit Test Suite
Runs in ~15 seconds with zero external model dependencies (uses deterministic stubbing):
```powershell
python -m pytest -q
```
*Expected: 127 passed, 9 skipped*

### Ruff Code Linter
```powershell
python -m ruff check .
```
*Expected: All checks passed!*

### Privacy and Offline Audit
Verifies network socket isolation and absence of log leaks:
```powershell
python scripts/privacy_check.py
```
*Expected: AUDIT RESULT: PASSED*

### Real Gemma 3n E2B Integration Tests (Opt-in)
Executes end-to-end inference against the real local Ollama Gemma 3n instance:
```powershell
# Windows PowerShell
$env:TRIAGE_RUN_REAL_MODEL="1"
python -m pytest tests/integration/test_real_gemma.py -v

# Linux / Bash
TRIAGE_RUN_REAL_MODEL=1 python -m pytest tests/integration/test_real_gemma.py -v
```
*Expected: 8 passed, 1 skipped (switching skipped if e4b not installed)*

---

## 5. Running CUAD Benchmarks & Evaluations

### CUAD Clause Retrieval Evaluation
Evaluates BM25 retrieval against the Atticus Project's CUAD dataset:
```powershell
python eval/retrieval_eval.py --subset 40
```
*Results output to: `reports/cuad_retrieval_bm25.md` & `.json`*

### Grounded Q&A Evaluation
Evaluates question answering with synthetic contracts, comparing retrieval-only and real Gemma 3n models:
```powershell
# Retrieval-only validation
python eval/answer_eval.py --retrieval-only

# Real model evaluation
python eval/answer_eval.py --model gemma3n:e2b
```
*Results output to: `reports/answer_eval_*.md` & `.json`*

