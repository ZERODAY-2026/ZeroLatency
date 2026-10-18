from dataclasses import dataclass, replace
from typing import Protocol, TypeVar

import requests
from pydantic import BaseModel, ValidationError

from .config import SUPPORTED_MODELS, Settings
from .config import settings as default_settings
from .errors import (
    InsufficientMemory,
    InvalidModelOutput,
    ModelError,
    ModelMissing,
    ModelTimeout,
    OllamaUnavailable,
)
from .models import pull_hint, validate_model
from .privacy import assert_loopback_url

T = TypeVar("T", bound=BaseModel)


class ChatClient(Protocol):
    """Minimum interface for inference. Real clients may also offer with_model()/prepare_model()."""

    def chat_json(self, system: str, user: str, schema: dict) -> str: ...


@dataclass
class StructuredStats:
    """Optional counters; attach as `client.stats` to measure structured-output validity."""

    calls: int = 0
    first_try_valid: int = 0
    valid: int = 0
    failed: int = 0


class OllamaClient:
    def __init__(
        self,
        cfg: Settings = default_settings,
        session: requests.Session | None = None,
        model: str | None = None,
    ):
        self.cfg = cfg
        self.model = validate_model(model if model is not None else cfg.model)
        self.base_url = assert_loopback_url(cfg.ollama_url)
        self.timeout = cfg.request_timeout
        self.num_ctx = cfg.num_ctx
        self.session = session or requests.Session()
        self.session.trust_env = False

    # ---- explicit model selection -------------------------------------------------
    def with_model(self, model: str) -> "OllamaClient":
        """A client bound to another allowlisted model. Shares the HTTP session; no other state."""
        return OllamaClient(replace(self.cfg, model=validate_model(model)), session=self.session)

    def prepare_model(self, model: str) -> None:
        """Make `model` the only allowlisted model resident in the runtime.

        Raises ModelMissing (with the pull command) if it is not installed. Never falls back to
        another model. Unloading uses Ollama's documented keep_alive=0 request and is best effort;
        the real state is whatever /api/ps reports afterwards.
        """
        model = validate_model(model)
        if model not in set(self.installed_models()):
            raise ModelMissing(f"Model '{model}' is not installed. Run: {pull_hint(model)}")
        for name in self.loaded_models():
            if name != model and name in SUPPORTED_MODELS:
                self.unload(name)

    # ---- runtime inspection ---------------------------------------------------------
    def installed_models(self) -> list[str]:
        data = self._json(self._request("get", "/api/tags"))
        return [item.get("name", "") for item in data.get("models", [])]

    def loaded_models(self) -> list[str]:
        data = self._json(self._request("get", "/api/ps"))
        return [item.get("name", "") for item in data.get("models", [])]

    def running_details(self) -> list[dict]:
        return list(self._json(self._request("get", "/api/ps")).get("models", []))

    def version(self) -> str | None:
        return self._json(self._request("get", "/api/version")).get("version")

    def show(self, model: str | None = None) -> dict:
        return self._json(self._request("post", "/api/show", json={"model": model or self.model}))

    def unload(self, model: str) -> None:
        validate_model(model)
        self._request("post", "/api/generate", json={"model": model, "keep_alive": 0})

    def check_ready(self) -> None:
        names = set(self.installed_models())
        wanted = {self.model, f"{self.model}:latest"}
        if not wanted & names:
            raise ModelMissing(f"Model '{self.model}' is not installed. Run: {pull_hint(self.model)}")

    # ---- inference ----------------------------------------------------------------
    def chat_json(self, system: str, user: str, schema: dict) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "format": schema,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {"temperature": 0, "num_ctx": self.num_ctx},
        }
        response = self._request("post", "/api/chat", json=payload)
        try:
            return response.json()["message"]["content"]
        except (ValueError, KeyError, TypeError):
            raise InvalidModelOutput("The model server returned an unexpected response.") from None

    @staticmethod
    def _json(response: requests.Response) -> dict:
        try:
            data = response.json()
        except ValueError:
            raise InvalidModelOutput("The model server returned an unexpected response.") from None
        if not isinstance(data, dict):
            raise InvalidModelOutput("The model server returned an unexpected response.")
        return data

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        try:
            response = getattr(self.session, method)(f"{self.base_url}{path}", timeout=self.timeout, **kwargs)
        except requests.Timeout:
            raise ModelTimeout("The local model took too long to respond.") from None
        except requests.ConnectionError:
            raise OllamaUnavailable(
                "Cannot reach Ollama at the local endpoint. Start it with: ollama serve"
            ) from None
        if response.status_code == 404:
            raise ModelMissing(f"Model '{self.model}' is not installed. Run: {pull_hint(self.model)}")
        if response.status_code >= 400:
            if response.status_code >= 500 and _mentions_memory(response):
                raise InsufficientMemory(
                    f"The local runtime could not load '{self.model}' because it needs more memory "
                    "than is available. Close other applications or choose the smaller model."
                )
            raise ModelError(f"The local model server returned status {response.status_code}.")
        return response


def _mentions_memory(response) -> bool:
    try:
        body = response.json()
    except ValueError:
        return False
    message = body.get("error", "") if isinstance(body, dict) else ""
    return isinstance(message, str) and "memory" in message.lower()


def call_structured[T: BaseModel](
    client: ChatClient, system: str, user: str, model_cls: type[T], retries: int = 1
) -> T:
    schema = model_cls.model_json_schema()
    stats = getattr(client, "stats", None)
    stats = stats if isinstance(stats, StructuredStats) else None
    if stats:
        stats.calls += 1
    for attempt in range(retries + 1):
        raw = client.chat_json(system, user, schema)
        try:
            parsed = model_cls.model_validate_json(raw)
        except ValidationError:
            continue
        if stats:
            stats.valid += 1
            stats.first_try_valid += attempt == 0
        return parsed
    if stats:
        stats.failed += 1
    raise InvalidModelOutput(
        f"Model output did not match the {model_cls.__name__} schema after {retries + 1} attempts."
    )
