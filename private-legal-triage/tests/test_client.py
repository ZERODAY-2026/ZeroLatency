from unittest.mock import MagicMock

import pytest
import requests

from src.config import Settings
from src.errors import (
    InvalidModelOutput,
    ModelMissing,
    ModelTimeout,
    OllamaUnavailable,
    PrivacyViolation,
)
from src.gemma_client import OllamaClient, call_structured
from src.schemas import SummaryOut


def client_with(session):
    return OllamaClient(Settings(), session=session)


def response(status=200, payload=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload if payload is not None else {}
    return r


def test_remote_endpoint_rejected():
    with pytest.raises(PrivacyViolation):
        OllamaClient(Settings(ollama_url="https://api.example.com"))


def test_env_proxies_are_ignored():
    assert client_with(requests.Session()).session.trust_env is False


def test_connection_error_maps_to_unavailable():
    session = MagicMock()
    session.post.side_effect = requests.ConnectionError("boom")
    with pytest.raises(OllamaUnavailable):
        client_with(session).chat_json("s", "u", {})


def test_timeout_maps_to_model_timeout():
    session = MagicMock()
    session.post.side_effect = requests.Timeout("slow")
    with pytest.raises(ModelTimeout):
        client_with(session).chat_json("s", "u", {})


def test_404_maps_to_model_missing():
    session = MagicMock()
    session.post.return_value = response(404)
    with pytest.raises(ModelMissing):
        client_with(session).chat_json("s", "u", {})


def test_success_returns_content_and_sends_schema():
    session = MagicMock()
    session.post.return_value = response(200, {"message": {"content": '{"summary": "x"}'}})
    out = client_with(session).chat_json("sys", "usr", {"type": "object"})
    assert out == '{"summary": "x"}'
    sent = session.post.call_args.kwargs["json"]
    assert sent["format"] == {"type": "object"}
    assert sent["stream"] is False
    assert sent["options"]["temperature"] == 0
    assert session.post.call_args.args[0].startswith("http://127.0.0.1")


def test_unexpected_payload():
    session = MagicMock()
    session.post.return_value = response(200, {"oops": 1})
    with pytest.raises(InvalidModelOutput):
        client_with(session).chat_json("s", "u", {})


def test_check_ready_detects_missing_model():
    session = MagicMock()
    session.get.return_value = response(200, {"models": [{"name": "llama3:8b"}]})
    with pytest.raises(ModelMissing):
        client_with(session).check_ready()


def test_check_ready_accepts_installed_model():
    session = MagicMock()
    session.get.return_value = response(200, {"models": [{"name": "gemma3n:e2b"}]})
    client_with(session).check_ready()


def test_call_structured_retries_then_succeeds():
    outputs = iter(["nope", '{"summary": "ok"}'])
    fake = MagicMock()
    fake.chat_json.side_effect = lambda *a: next(outputs)
    assert call_structured(fake, "s", "u", SummaryOut).summary == "ok"
