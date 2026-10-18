"""P1.7: failure modes, cleanup and 'errors never leak document text'."""

import logging

import pytest

from samples.make_samples import write_pdf
from src.config import Settings
from src.errors import (
    AnalysisCancelled,
    DocumentError,
    InvalidModelOutput,
    ModelTimeout,
    OllamaUnavailable,
    UnreadableDocument,
)
from src.gemma_client import OllamaClient
from src.pipeline import DocumentSession
from src.privacy import PrivateWorkspace
from tests.helpers import rental_responder
from tests.stub_ollama import StubOllama

CANARY = "ZXQ-CANARY-7731 confidential clause about the tenant's secret deposit"
BODY = f"1. TERM\nThe lease runs for eleven months. {CANARY}.\n\n2. RENT\nRent is Rs. 25,000 monthly. " * 4


@pytest.fixture
def canary_txt(tmp_path):
    path = tmp_path / "canary.txt"
    path.write_text(BODY, encoding="utf-8")
    return path


def test_oversized_file_rejected(tmp_path):
    path = tmp_path / "big.txt"
    path.write_text("x" * 5000)
    with pytest.raises(UnreadableDocument):
        DocumentSession(path, object(), Settings(max_file_bytes=1000))


def test_pdf_over_page_limit_rejected(tmp_path):
    path = write_pdf(tmp_path / "long.pdf", ["Clause text here. " * 20] * 4)
    with pytest.raises(UnreadableDocument):
        DocumentSession(path, object(), Settings(max_pdf_pages=2))


def test_chunk_count_is_bounded(canary_txt):
    with pytest.raises(UnreadableDocument):
        DocumentSession(canary_txt, object(), Settings(max_chunks=1, chunk_max_chars=100))


def test_empty_and_whitespace_documents(tmp_path):
    for content in ("", "   \n\n  "):
        path = tmp_path / "e.txt"
        path.write_text(content)
        with pytest.raises(DocumentError):
            DocumentSession(path, object())


def test_missing_ollama_gives_actionable_error(canary_txt):
    cfg = Settings(ollama_url="http://127.0.0.1:9")
    session = DocumentSession(canary_txt, OllamaClient(cfg), cfg)
    with pytest.raises(OllamaUnavailable) as err:
        session.analyze()
    assert "ollama serve" in str(err.value) and CANARY not in str(err.value)


def test_timeout_is_reported_and_leaks_nothing(canary_txt):
    with StubOllama(responder=rental_responder) as stub:
        stub.delay = 0.5
        cfg = Settings(ollama_url=stub.url, request_timeout=0.1)
        session = DocumentSession(canary_txt, OllamaClient(cfg), cfg)
        with pytest.raises(ModelTimeout) as err:
            session.analyze()
        assert CANARY not in str(err.value)
        assert session.result is None  # no success fabricated


def test_malformed_output_everywhere_fails_loudly_without_content(canary_txt):
    with StubOllama() as stub:
        stub.raw_reply = f"not json {CANARY}"
        cfg = Settings(ollama_url=stub.url)
        session = DocumentSession(canary_txt, OllamaClient(cfg), cfg)
        with pytest.raises(InvalidModelOutput) as err:
            session.analyze()
        assert CANARY not in str(err.value)
        assert session.result is None


def test_partial_chunk_failure_is_recorded_not_hidden(canary_txt):
    calls = {"n": 0}

    def flaky(model, system, user):
        if user.startswith("Section notes"):
            return '{"summary": "ok"}'
        calls["n"] += 1
        return "garbage" if calls["n"] <= 2 else '{"chunk_summary": "fine", "findings": []}'

    with StubOllama(responder=flaky) as stub:
        cfg = Settings(ollama_url=stub.url, chunk_max_chars=120)
        session = DocumentSession(canary_txt, OllamaClient(cfg), cfg)
        result = session.analyze()
    assert any("could not be analysed" in note for note in result.limitations)


def test_cancellation_discards_result_and_keeps_document(canary_txt):
    with StubOllama(responder=rental_responder) as stub:
        cfg = Settings(ollama_url=stub.url, chunk_max_chars=120)
        session = DocumentSession(canary_txt, OllamaClient(cfg), cfg)
        seen = []

        def progress(done, total):
            seen.append(done)

        with pytest.raises(AnalysisCancelled):
            session.analyze(progress, should_cancel=lambda: len(seen) >= 1)
        assert session.result is None and len(seen) == 1
        assert session.analyze().findings is not None  # session still usable


def test_workspace_is_cleaned_after_exception(tmp_path):
    root = None
    with pytest.raises(RuntimeError), PrivateWorkspace() as ws:
        root = ws.root
        ws.save_upload("a.txt", b"secret")
        raise RuntimeError("boom")
    assert root is not None and not root.exists()


def test_delete_file_overwrites_then_removes(tmp_path):
    with PrivateWorkspace() as ws:
        path = ws.save_upload("a.txt", b"secret-bytes")
        ws.delete_file(path)
        assert not path.exists()


def test_no_document_text_in_logs_or_errors(canary_txt, caplog):
    caplog.set_level(logging.DEBUG)
    with StubOllama(responder=rental_responder) as stub:
        stub.raw_reply = "garbage"
        cfg = Settings(ollama_url=stub.url)
        session = DocumentSession(canary_txt, OllamaClient(cfg), cfg)
        with pytest.raises(InvalidModelOutput):
            session.analyze()
    assert CANARY not in caplog.text
