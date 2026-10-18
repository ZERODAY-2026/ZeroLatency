"""Opt-in integration tests against a REAL local Ollama + Gemma 3n model.

Run:   TRIAGE_RUN_REAL_MODEL=1 python -m pytest tests/integration -m real_model -s -p no:cacheprovider
       (PowerShell:  $env:TRIAGE_RUN_REAL_MODEL="1"; python -m pytest tests/integration -m real_model -s)
Pick the model under test with TRIAGE_REAL_MODEL (default gemma3n:e2b). Only one model is used at a
time. Nothing here runs in the normal unit-test run, which needs neither Ollama nor model weights.
"""

import os
import time

import pytest

from scripts.hardware import PeakSampler, system_info
from src.citation_validator import normalize
from src.config import SUPPORTED_MODELS, Settings
from src.errors import ModelMissing, ModelTimeout, OllamaUnavailable
from src.gemma_client import OllamaClient, StructuredStats, call_structured
from src.pipeline import DocumentSession
from src.schemas import ChunkAnalysis
from src.triage import SYSTEM_PROMPT

pytestmark = pytest.mark.real_model

MODEL = os.getenv("TRIAGE_REAL_MODEL", "gemma3n:e2b")

# Synthetic contract. Page 1 and page 2 are separated by a form feed, so page numbers are known.
PAGE1 = """EMPLOYMENT AGREEMENT (SYNTHETIC TEST FIXTURE)

1. POSITION AND PAY
The Employee will work as a Junior Analyst. The Employee shall receive a gross monthly salary of Rs. 60,000, payable on the last working day of each month.

2. PROBATION
The first six months of employment form a probation period. During probation either party may end the employment by giving 7 days' written notice."""
PAGE2 = """3. TERMINATION
After probation, the Employee may resign by giving 45 days' written notice. The Company may terminate the Employee for gross misconduct without notice.

4. NON-COMPETE
For 12 months after leaving the Company, the Employee shall not work for a direct competitor within the city of Sampletown.

5. GOVERNING LAW
This agreement is governed by the laws of India."""
FIXTURE = PAGE1 + "\f" + PAGE2
KNOWN = {"salary": "60,000", "notice": "45", "non_compete": "12 months"}


@pytest.fixture(scope="module")
def cfg():
    return Settings(model=MODEL, request_timeout=float(os.getenv("TRIAGE_TIMEOUT", "600")))


@pytest.fixture(scope="module")
def client(cfg):
    stats = StructuredStats()
    c = OllamaClient(cfg)
    c.stats = stats
    return c


@pytest.fixture
def fixture_path(tmp_path):
    path = tmp_path / "employment.txt"
    path.write_text(FIXTURE, encoding="utf-8")
    return path


def test_ollama_service_available(client, run_log):
    try:
        version = client.version()
    except OllamaUnavailable:
        pytest.fail("Ollama is not reachable at the configured loopback URL. Start it: ollama serve")
    run_log["results"]["ollama_version"] = version
    run_log["results"]["system"] = system_info()
    assert version


def test_selected_model_is_installed(client, run_log):
    try:
        client.check_ready()
    except ModelMissing as error:
        pytest.fail(str(error))
    details = client.show().get("details", {})
    run_log["results"]["model"] = {
        "id": MODEL,
        "quantization": details.get("quantization_level", "not reported"),
        "parameter_size": details.get("parameter_size", "not reported"),
        "format": details.get("format", "not reported"),
        "num_ctx_configured": client.num_ctx,
        "temperature": 0,
    }


def test_missing_model_is_reported_not_substituted(client):
    other = next((m for m in SUPPORTED_MODELS if m not in set(client.installed_models())), None)
    if other is None:
        pytest.skip("Both supported models are installed, so a missing-model case cannot be observed.")
    with pytest.raises(ModelMissing) as err:
        client.prepare_model(other)
    assert f"ollama pull {other}" in str(err.value)


def test_timeout_is_graceful(cfg):
    from dataclasses import replace

    tiny = OllamaClient(replace(cfg, request_timeout=0.001))
    with pytest.raises((ModelTimeout, OllamaUnavailable)):
        tiny.chat_json("s", "u", {"type": "object"})


def test_real_inference_structured_output(client, run_log):
    client.prepare_model(MODEL)
    started = time.perf_counter()
    with PeakSampler() as sampler:
        result = call_structured(
            client, SYSTEM_PROMPT, f'<document_passage page="1">\n{PAGE1}\n</document_passage>', ChunkAnalysis
        )
    latency = time.perf_counter() - started
    assert isinstance(result, ChunkAnalysis)
    run_log["results"]["single_chunk_call"] = {
        "latency_seconds": round(latency, 2),
        "findings_returned": len(result.findings),
        "resources": sampler.summary(),
        "runtime_reported_model_memory": client.running_details(),
    }


def test_full_pipeline_citations_and_pages(fixture_path, cfg, client, run_log):
    session = DocumentSession(fixture_path, client, cfg)
    with PeakSampler() as sampler:
        result = session.analyze(model=MODEL)
    pages = {p.number: normalize(p.text) for p in session.pages}
    assert result.findings, "The real model returned no findings for a fixture with obvious clauses."
    verified = [f for f in result.findings if f.verification_status == "verified"]
    for finding in verified:  # independent re-check, not the validator's own verdict
        assert finding.page in pages
        assert normalize(finding.evidence_quote.strip("\"' ")) in pages[finding.page]
    assert all(f.page in pages or f.verification_status == "unverified" for f in result.findings)
    run_log["results"]["full_pipeline"] = {
        "latency_seconds": result.elapsed_seconds,
        "findings": len(result.findings),
        "verified": len(verified),
        "citation_validity_rate": round(len(verified) / len(result.findings), 3),
        "structured_output": vars(client.stats),
        "resources": sampler.summary(),
        "limitations": result.limitations,
    }
    assert verified, "No finding had a verifiable quotation."


def test_question_answering_recorded(fixture_path, cfg, client, run_log):
    session = DocumentSession(fixture_path, client, cfg)
    answer = session.ask("How many days' notice must the employee give to resign after probation?", model=MODEL)
    if answer.answerable:
        assert any(e.verification_status == "verified" for e in answer.evidence)
    run_log["results"]["qa_notice"] = {
        "answerable": answer.answerable,
        "contains_expected_fact_45": KNOWN["notice"] in answer.answer,  # recorded, not asserted
        "evidence_verified": [e.verification_status for e in answer.evidence],
    }


def test_only_selected_model_is_resident(client, run_log):
    client.prepare_model(MODEL)
    client.with_model(MODEL).chat_json("Reply with JSON.", "{}", {"type": "object"})
    resident = [m for m in client.loaded_models() if m in SUPPORTED_MODELS]
    run_log["results"]["resident_after_inference"] = resident
    assert resident == [MODEL]


def test_switching_between_models_if_both_installed(client, run_log):
    if not set(SUPPORTED_MODELS) <= set(client.installed_models()):
        pytest.skip("Both Gemma 3n models must be installed to test switching.")
    observed = {}
    for model in (*SUPPORTED_MODELS, next(iter(SUPPORTED_MODELS))):
        client.prepare_model(model)
        client.with_model(model).chat_json("Reply with JSON.", "{}", {"type": "object"})
        observed.setdefault(model, []).append([m for m in client.loaded_models() if m in SUPPORTED_MODELS])
        assert observed[model][-1] == [model]
    run_log["results"]["switching_residency"] = observed
