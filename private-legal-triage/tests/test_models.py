import pytest

from src.config import Settings
from src.errors import (
    InsufficientMemory,
    ModelMissing,
    OllamaUnavailable,
    UnsupportedModel,
)
from src.gemma_client import OllamaClient
from src.models import models_status, validate_model
from src.pipeline import DocumentSession
from tests.helpers import rental_responder
from tests.stub_ollama import StubOllama

E2B, E4B = "gemma3n:e2b", "gemma3n:e4b"


def cfg_for(stub, **kw):
    return Settings(ollama_url=stub.url, **kw)


@pytest.mark.parametrize("bad", ["llama3:8b", "gemma3n:e2b ", "GEMMA3N:E2B", "http://evil.example/m", "", None, 7, "../x"])
def test_allowlist_rejects_everything_else(bad):
    with pytest.raises(UnsupportedModel):
        validate_model(bad)


def test_allowlist_accepts_both_gemma_sizes():
    assert validate_model(E2B) == E2B and validate_model(E4B) == E4B


def test_env_model_must_be_allowlisted():
    with pytest.raises(UnsupportedModel):
        OllamaClient(Settings(model="llama3:8b"))


def test_requested_model_is_sent_to_runtime():
    with StubOllama(installed=[E2B, E4B], responder=rental_responder) as stub:
        client = OllamaClient(cfg_for(stub))
        client.with_model(E4B).chat_json("s", "u", {})
        client.chat_json("s", "u", {})
        assert stub.chat_models_used() == [E4B, E2B]


def test_missing_model_reports_pull_command_and_does_not_fall_back():
    with StubOllama(installed=[E2B], responder=rental_responder) as stub:
        client = OllamaClient(cfg_for(stub))
        with pytest.raises(ModelMissing) as err:
            client.prepare_model(E4B)
        assert f"ollama pull {E4B}" in str(err.value)
        assert stub.chat_models_used() == []
        with pytest.raises(ModelMissing):
            client.with_model(E4B).chat_json("s", "u", {})  # runtime 404, still no fallback
        assert stub.chat_models_used() == [E4B]


def test_switching_unloads_previous_gemma_but_not_foreign_models():
    with StubOllama(installed=[E2B, E4B], responder=rental_responder) as stub:
        stub.loaded = [E2B, "someone-elses-model:7b"]
        OllamaClient(cfg_for(stub)).prepare_model(E4B)
        unloads = [b for m, p, b in stub.requests if p == "/api/generate"]
        assert unloads == [{"model": E2B, "keep_alive": 0}]
        assert "someone-elses-model:7b" in stub.loaded and E2B not in stub.loaded


def test_only_selected_model_resident_after_switch_roundtrip():
    with StubOllama(installed=[E2B, E4B], responder=rental_responder) as stub:
        client = OllamaClient(cfg_for(stub))
        for model in (E2B, E4B, E2B):
            client.prepare_model(model)
            client.with_model(model).chat_json("s", "u", {})
            assert client.loaded_models() == [model]


def test_insufficient_memory_is_reported_clearly():
    with StubOllama(installed=[E4B], too_big=[E4B]) as stub:
        with pytest.raises(InsufficientMemory) as err:
            OllamaClient(cfg_for(stub)).with_model(E4B).chat_json("s", "u", {})
        assert "memory" in str(err.value).lower() and "9.0" not in str(err.value)


def test_status_reports_availability_honestly():
    with StubOllama(installed=[E2B]) as stub:
        stub.loaded = [E2B]
        status = models_status(OllamaClient(cfg_for(stub)), E2B)
    by_id = {m.id: m for m in status.models}
    assert status.ollama_available and status.ollama_version == "stub-0.0"
    assert by_id[E2B].installed and by_id[E2B].loaded and by_id[E2B].setup_hint is None
    assert not by_id[E4B].installed and by_id[E4B].setup_hint == f"ollama pull {E4B}"


def test_status_when_ollama_is_down():
    client = OllamaClient(Settings(ollama_url="http://127.0.0.1:9"))  # nothing listens on port 9
    status = models_status(client, E2B)
    assert not status.ollama_available
    assert all(not m.installed for m in status.models)
    assert "ollama serve" in status.message
    with pytest.raises(OllamaUnavailable):
        client.installed_models()


# ---- DocumentSession: explicit selection without reprocessing -----------------------------
def test_switching_models_keeps_document_state_and_never_reprocesses(rental_txt, monkeypatch):
    with StubOllama(installed=[E2B, E4B], responder=rental_responder) as stub:
        session = DocumentSession(rental_txt, OllamaClient(cfg_for(stub)), cfg_for(stub))
        pages, chunks, index, retriever = session.pages, session.chunks, session.index, session.retriever

        def boom(*a, **k):
            raise AssertionError("document was reprocessed")

        monkeypatch.setattr("src.pipeline.extract_pages", boom)
        monkeypatch.setattr("src.pipeline.chunk_pages", boom)
        first = session.analyze(model=E2B)
        second = session.analyze(model=E4B)
        answer = session.ask("What is the security deposit?", model=E4B)

        assert (first.model, second.model, answer.model) == (E2B, E4B, E4B)
        assert session.pages is pages and session.chunks is chunks
        assert session.index is index and session.retriever is retriever
        used = stub.chat_models_used()
        assert used.count(E2B) > 0 and used.count(E4B) > 0
        assert used == sorted(used, key=lambda m: m == E4B)  # all E2B calls precede all E4B calls
        assert stub.loaded == [E4B]  # previous model was released


def test_unsupported_model_rejected_before_any_runtime_call(rental_txt):
    with StubOllama(installed=[E2B], responder=rental_responder) as stub:
        session = DocumentSession(rental_txt, OllamaClient(cfg_for(stub)), cfg_for(stub))
        with pytest.raises(UnsupportedModel):
            session.analyze(model="llama3:8b")
        with pytest.raises(UnsupportedModel):
            session.ask("What is the deposit?", model="http://example.com/x")
        assert stub.requests == []


def test_unavailable_selected_model_is_not_silently_replaced(rental_txt):
    with StubOllama(installed=[E2B], responder=rental_responder) as stub:
        session = DocumentSession(rental_txt, OllamaClient(cfg_for(stub)), cfg_for(stub))
        with pytest.raises(ModelMissing):
            session.analyze(model=E4B)
        assert stub.chat_models_used() == []
        assert session.result is None


def test_default_model_used_when_none_requested(rental_txt):
    with StubOllama(installed=[E2B, E4B], responder=rental_responder) as stub:
        session = DocumentSession(rental_txt, OllamaClient(cfg_for(stub)), cfg_for(stub))
        assert session.analyze().model == E2B
        assert set(stub.chat_models_used()) == {E2B}
