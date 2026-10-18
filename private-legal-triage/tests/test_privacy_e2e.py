"""End-to-end run (upload -> analyse -> ask -> delete) under network_guard against a loopback stub.

This proves Python-level behaviour only. It does not prove OS-level isolation or real Ollama
behaviour; see docs/PRIVACY.md and scripts/privacy_check.py for those procedures.
"""

import logging

from src.config import Settings
from src.gemma_client import OllamaClient
from src.privacy import network_guard
from src.service import DocumentStore
from tests.conftest import RENTAL_PAGES
from tests.helpers import rental_responder
from tests.stub_ollama import StubOllama

TEXT = "\n\n".join(RENTAL_PAGES).encode()


def test_full_flow_touches_only_loopback_and_leaves_nothing(caplog):
    caplog.set_level(logging.DEBUG)
    observed: list[str] = []
    with StubOllama(installed=["gemma3n:e2b", "gemma3n:e4b"], responder=rental_responder) as stub:
        cfg = Settings(ollama_url=stub.url)
        with network_guard(observed) as blocked:
            store = DocumentStore(cfg, OllamaClient(cfg))
            root = store._workspace.root
            doc = store.upload("lease.txt", TEXT)
            job = store.wait(store.start_analysis(doc.id, model="gemma3n:e4b").id)
            answer = store.ask(doc.id, "What is the security deposit?", model="gemma3n:e2b")
            store.delete(doc.id)
            store.close()
    assert blocked == []
    assert observed and set(observed) == {"127.0.0.1"}
    assert job.state == "completed" and answer.answerable
    assert not root.exists()
    for marker in ("refundable security deposit", "Asha Rao", "Rs. 25,000"):
        assert marker not in caplog.text
