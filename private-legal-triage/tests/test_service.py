import time

import pytest

from src.config import Settings
from src.errors import (
    Busy,
    DocumentNotFound,
    EmptyQuestion,
    LimitExceeded,
    NoExtractableText,
    UnreadableDocument,
    UnsupportedFormat,
    UnsupportedModel,
)
from src.gemma_client import OllamaClient
from src.service import DocumentStore
from tests.conftest import RENTAL_PAGES
from tests.helpers import rental_responder
from tests.stub_ollama import StubOllama

E2B, E4B = "gemma3n:e2b", "gemma3n:e4b"
TEXT = "\n\n".join(RENTAL_PAGES).encode()


@pytest.fixture
def env():
    with StubOllama(installed=[E2B, E4B], responder=rental_responder) as stub:
        cfg = Settings(ollama_url=stub.url, chunk_max_chars=500)
        store = DocumentStore(cfg, OllamaClient(cfg))
        try:
            yield stub, store
        finally:
            store.close()


def wait_until(predicate, timeout=10.0):
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_upload_list_metadata_and_stable_ids(env):
    _, store = env
    info = store.upload("lease.txt", TEXT)
    assert store.get(info.id) == info and info.pages >= 1 and info.chunks >= 2
    assert [d.id for d in store.list_documents()] == [info.id]
    assert store.upload("lease.txt", TEXT).id != info.id


def test_upload_validation(env):
    _, store = env
    with pytest.raises(UnsupportedFormat):
        store.upload("x.docx", b"abc")
    with pytest.raises(UnreadableDocument):
        store.upload("x.txt", b"")
    with pytest.raises(NoExtractableText):
        store.upload("x.txt", b"tiny")  # too little text
    assert store.list_documents() == []


def test_upload_size_and_count_limits():
    with StubOllama() as stub:
        cfg = Settings(ollama_url=stub.url, max_file_bytes=100, max_documents=1)
        store = DocumentStore(cfg, OllamaClient(cfg))
        with pytest.raises(LimitExceeded):
            store.upload("big.txt", b"x" * 101)
        store.close()
        cfg = Settings(ollama_url=stub.url, max_documents=1)
        store = DocumentStore(cfg, OllamaClient(cfg))
        store.upload("a.txt", TEXT)
        with pytest.raises(LimitExceeded):
            store.upload("b.txt", TEXT)
        store.close()


def test_failed_upload_leaves_no_file_behind(env):
    _, store = env
    root = store._workspace.root
    with pytest.raises(UnreadableDocument):
        store.upload("bad.pdf", b"not a pdf")
    assert list(root.iterdir()) == []


def test_search_returns_passages_with_pages(env):
    _, store = env
    doc = store.upload("lease.txt", TEXT)
    hits = store.search(doc.id, "security deposit refundable", k=2)
    assert hits and "deposit" in hits[0].text.lower() and hits[0].page >= 1
    assert store.page(doc.id, hits[0].page).text
    with pytest.raises(EmptyQuestion):
        store.search(doc.id, "  ")
    with pytest.raises(DocumentNotFound):
        store.page(doc.id, 99)


def test_analysis_job_progress_and_result(env):
    stub, store = env
    doc = store.upload("lease.txt", TEXT)
    job = store.start_analysis(doc.id, model=E4B)
    final = store.wait(job.id)
    assert final.state == "completed" and final.stage == "done"
    assert final.sections_done == final.sections_total == doc.chunks
    assert final.result.model == E4B and final.result.findings
    assert set(stub.chat_models_used()) == {E4B}
    assert store.result(doc.id).model == E4B
    assert store.get(doc.id).analyzed


def test_unsupported_model_rejected_without_starting_job(env):
    stub, store = env
    doc = store.upload("lease.txt", TEXT)
    with pytest.raises(UnsupportedModel):
        store.start_analysis(doc.id, model="llama3:8b")
    with pytest.raises(UnsupportedModel):
        store.ask(doc.id, "What is the deposit?", model="x")
    assert stub.chat_models_used() == []
    store.start_analysis(doc.id)  # gate must not be left locked by the rejections


def test_cancellation_is_honest_and_discards_partial_result(env):
    stub, store = env
    stub.delay = 0.25
    doc = store.upload("lease.txt", TEXT)
    job = store.start_analysis(doc.id)
    assert wait_until(lambda: store.job(job.id).sections_done >= 1)
    store.cancel(job.id)
    final = store.wait(job.id)
    assert final.state == "cancelled" and final.result is None
    assert final.sections_done < doc.chunks  # it really stopped early
    with pytest.raises(DocumentNotFound):
        store.result(doc.id)
    store.start_analysis(doc.id)  # model gate released after cancellation


def test_concurrent_requests_are_rejected_not_queued_silently(env):
    stub, store = env
    stub.delay = 0.2
    doc = store.upload("lease.txt", TEXT)
    job = store.start_analysis(doc.id)
    with pytest.raises(Busy):
        store.start_analysis(doc.id)
    with pytest.raises(Busy):
        store.ask(doc.id, "What is the security deposit?")
    store.cancel(job.id)
    store.wait(job.id)
    assert store.ask(doc.id, "What is the security deposit?").answerable


def test_failed_job_reports_safe_error(env):
    stub, store = env
    stub.raw_reply = "garbage"
    doc = store.upload("lease.txt", TEXT)
    final = store.wait(store.start_analysis(doc.id).id)
    assert final.state == "failed" and final.error_code == "InvalidModelOutput"
    assert final.result is None


def test_job_with_missing_model_fails_with_setup_hint():
    with StubOllama(installed=[E2B], responder=rental_responder) as stub:
        cfg = Settings(ollama_url=stub.url)
        store = DocumentStore(cfg, OllamaClient(cfg))
        doc = store.upload("lease.txt", TEXT)
        final = store.wait(store.start_analysis(doc.id, model=E4B).id)
        store.close()
    assert final.state == "failed" and final.error_code == "ModelMissing"
    assert f"ollama pull {E4B}" in final.error_message
    assert stub.chat_models_used() == []


def test_delete_removes_file_index_jobs_and_access(env):
    _, store = env
    doc = store.upload("lease.txt", TEXT)
    record = store._docs[doc.id]
    job = store.start_analysis(doc.id)
    store.wait(job.id)
    session, path = record.session, record.path
    assert path.exists()
    store.delete(doc.id)
    assert not path.exists()
    assert list(store._workspace.root.iterdir()) == []
    assert session.chunks == [] and session.pages == [] and session.result is None
    assert session.retriever is None and session.index is None
    for call in (
        lambda: store.get(doc.id),
        lambda: store.search(doc.id, "deposit"),
        lambda: store.ask(doc.id, "deposit?"),
        lambda: store.job(job.id),
        lambda: store.result(doc.id),
        lambda: store.delete(doc.id),
    ):
        with pytest.raises(DocumentNotFound):
            call()


def test_delete_during_running_analysis(env):
    stub, store = env
    stub.delay = 0.15
    doc = store.upload("lease.txt", TEXT)
    store.start_analysis(doc.id)
    store.delete(doc.id)  # cancels, waits, cleans
    assert store.list_documents() == []
    store.start_analysis(store.upload("again.txt", TEXT).id)  # gate free again


def test_close_removes_workspace(env):
    _, store = env
    store.upload("lease.txt", TEXT)
    root = store._workspace.root
    store.close()
    assert not root.exists() and store.list_documents() == []


def test_question_length_limit(env):
    _, store = env
    doc = store.upload("lease.txt", TEXT)
    with pytest.raises(LimitExceeded):
        store.ask(doc.id, "x" * 5000)
