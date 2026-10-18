from typing import Any

import requests

from .config import Settings
from .config import settings as default_settings
from .errors import ModelMissing, ModelTimeout, OllamaUnavailable, TriageError
from .privacy import assert_loopback_url


class EmbeddingError(TriageError):
    """Raised when an embedding request fails."""


class OllamaEmbeddingClient:
    def __init__(
        self,
        cfg: Settings = default_settings,
        model: str | None = None,
        timeout: float = 60.0,
    ):
        self.base_url = assert_loopback_url(cfg.ollama_url)
        self.model = model or cfg.embedding_model
        self.timeout = timeout

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of text strings in batch.

        Returns a list of float vectors matching the order of input texts.
        """
        if not texts:
            return []
        payload = {
            "model": self.model,
            "input": texts,
        }
        url = f"{self.base_url}/api/embed"
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
        except requests.exceptions.Timeout as exc:
            raise ModelTimeout(f"Embedding model timed out after {self.timeout}s.") from exc
        except requests.exceptions.ConnectionError as exc:
            raise OllamaUnavailable("Ollama is not running on loopback.") from exc
        except Exception as exc:
            raise EmbeddingError(f"Embedding request failed: {exc}") from exc

        if resp.status_code == 404:
            raise ModelMissing(
                f"Embedding model '{self.model}' is not installed in Ollama. Run: ollama pull {self.model}"
            )
        if resp.status_code != 200:
            raise EmbeddingError(f"Embedding API returned HTTP {resp.status_code}: {resp.text}")

        data: dict[str, Any] = resp.json()
        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            # Fallback to single-item queries if batch is not fully returned
            if len(texts) > 1:
                return [self.embed_query(t) for t in texts]
            raise EmbeddingError(f"Malformed embedding response from Ollama: {list(data.keys())}")

        return embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string.

        Returns a float vector.
        """
        cleaned = text.strip()
        if not cleaned:
            raise EmbeddingError("Cannot embed empty query.")
        payload = {
            "model": self.model,
            "input": cleaned,
        }
        url = f"{self.base_url}/api/embed"
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
        except requests.exceptions.Timeout as exc:
            raise ModelTimeout(f"Embedding model timed out after {self.timeout}s.") from exc
        except requests.exceptions.ConnectionError as exc:
            raise OllamaUnavailable("Ollama is not running on loopback.") from exc
        except Exception as exc:
            raise EmbeddingError(f"Embedding request failed: {exc}") from exc

        if resp.status_code == 404:
            raise ModelMissing(
                f"Embedding model '{self.model}' is not installed in Ollama. Run: ollama pull {self.model}"
            )
        if resp.status_code != 200:
            raise EmbeddingError(f"Embedding API returned HTTP {resp.status_code}: {resp.text}")

        data: dict[str, Any] = resp.json()
        embeddings = data.get("embeddings")
        if isinstance(embeddings, list) and embeddings:
            vec = embeddings[0]
            if isinstance(vec, list) and vec:
                return vec
        raise EmbeddingError(f"Malformed embedding response from Ollama: {list(data.keys())}")
