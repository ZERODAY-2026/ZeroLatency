import socket

import pytest
from fastapi.testclient import TestClient

from src.api import create_app
from src.config import Settings
from src.errors import PrivacyViolation
from src.gemma_client import OllamaClient
from src.service import DocumentStore
from tests.conftest import RENTAL_PAGES
from tests.helpers import rental_responder
from tests.stub_ollama import StubOllama

TEXT = "\n\n".join(RENTAL_PAGES).encode("utf-8")


def test_fastapi_lifecycle_and_privacy_guard():
    with StubOllama(installed=["gemma3n:e2b"], responder=rental_responder) as stub:
        cfg = Settings(ollama_url=stub.url)
        store = DocumentStore(cfg, OllamaClient(cfg))
        app = create_app(store)
        with TestClient(app) as client:
            # 1. Health check
            resp = client.get("/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"

            # 2. Upload document
            resp = client.post("/documents", files={"file": ("lease.txt", TEXT, "text/plain")})
            assert resp.status_code == 201
            doc_id = resp.json()["id"]

            # 3. Ask question
            resp = client.post(f"/documents/{doc_id}/ask", json={"question": "What is the rent?"})
            assert resp.status_code == 200
            assert resp.json()["answerable"] is True

            # 4. Verify external network calls fail with PrivacyViolation (HTTP 403)
            # Simulate an external egress attempt
            with pytest.raises(PrivacyViolation):
                socket.getaddrinfo("evil-external-tracker.com", 80)

            # 5. Delete document
            resp = client.delete(f"/documents/{doc_id}")
            assert resp.status_code == 204
