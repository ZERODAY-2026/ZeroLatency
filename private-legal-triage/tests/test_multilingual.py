"""Tests for local multilingual explanation capabilities."""

import json

import pytest
from fastapi.testclient import TestClient

from src.api import create_app
from src.config import Settings
from src.errors import UnsupportedLanguage
from src.gemma_client import OllamaClient
from src.privacy import network_guard
from src.service import DocumentStore
from tests.conftest import RENTAL_PAGES
from tests.stub_ollama import StubOllama

TEXT = "\n\n".join(RENTAL_PAGES).encode("utf-8")


def multilingual_responder(model, system, user):
    quotes = ["refundable security deposit of Rs. 75,000"]
    if "Hindi" in user:
        return json.dumps({
            "answerable": True,
            "answer": "जमानत राशि रु. 75,000 है और यह वापस करने योग्य है।",
            "evidence_quotes": quotes,
            "statement_type": "explicit",
            "jurisdiction_dependent": False,
        })
    return json.dumps({
        "answerable": True,
        "answer": "The deposit is Rs. 75,000 and refundable.",
        "evidence_quotes": quotes,
        "statement_type": "explicit",
        "jurisdiction_dependent": False,
    })


def test_multilingual_hindi_explanation_with_grounded_citation():
    with StubOllama(installed=["gemma3n:e2b"], responder=multilingual_responder) as stub:
        cfg = Settings(ollama_url=stub.url)
        store = DocumentStore(cfg, OllamaClient(cfg))
        doc = store.upload("lease.txt", TEXT)

        observed = []
        with network_guard(observed):
            answer = store.ask(doc.id, "How much notice is needed?", language="hi")

        assert answer.answerable is True
        assert answer.language == "hi"
        assert "जमानत राशि" in answer.answer
        # Evidence quotes MUST remain verbatim source text in English
        assert len(answer.evidence) == 1
        assert "refundable security deposit of Rs. 75,000" in answer.evidence[0].quote
        # Verified against English document
        assert answer.evidence[0].verification_status == "verified"

        # Verify no external calls were made
        assert all("127.0.0.1" in addr or "localhost" in addr for addr in observed)

        store.close()


def test_unsupported_language_raises_error():
    store = DocumentStore()
    doc = store.upload("lease.txt", TEXT)

    with pytest.raises(UnsupportedLanguage) as exc:
        store.ask(doc.id, "How much notice?", language="klingon")
    assert "klingon" in str(exc.value)

    store.close()


def test_multilingual_api_endpoint():
    with StubOllama(installed=["gemma3n:e2b"], responder=multilingual_responder) as stub:
        cfg = Settings(ollama_url=stub.url)
        store = DocumentStore(cfg, OllamaClient(cfg))
        app = create_app(store)
        doc = store.upload("lease.txt", TEXT)

        with TestClient(app) as client:
            # 1. Successful Hindi query
            resp = client.post(
                f"/documents/{doc.id}/ask",
                json={"question": "What is the deposit?", "language": "hi"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["language"] == "hi"
            assert "जमानत राशि" in data["answer"]
            assert data["evidence"][0]["verification_status"] == "verified"
            assert "refundable security deposit of Rs. 75,000" in data["evidence"][0]["quote"]

            # 2. Unsupported language query -> HTTP 400
            resp_bad = client.post(
                f"/documents/{doc.id}/ask",
                json={"question": "What is the notice period?", "language": "unsupported_lang"},
            )
            assert resp_bad.status_code == 400
            assert "UnsupportedLanguage" in resp_bad.json()["error"]["code"]

        store.close()
