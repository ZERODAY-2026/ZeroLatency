import contextlib
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.types import EmbeddingFunction, Embeddings
from chromadb.config import Settings as ChromaSettings

from .config import Settings
from .config import settings as default_settings
from .embedding_client import OllamaEmbeddingClient
from .errors import TriageError
from .schemas import Chunk


class VectorStoreError(TriageError):
    """Raised when vector store operations fail."""


class _OllamaChromaEmbeddingFunction(EmbeddingFunction[Any]):
    def __init__(self, embed_client: OllamaEmbeddingClient):
        self.client = embed_client

    def __call__(self, input: Any) -> Embeddings:
        if isinstance(input, str):
            input = [input]
        return self.client.embed_texts(list(input))

    def embed_query(self, input: Any) -> Embeddings:
        if isinstance(input, str):
            input = [input]
        return self.client.embed_texts(list(input))

    def embed_documents(self, input: Any) -> Embeddings:
        if isinstance(input, str):
            input = [input]
        return self.client.embed_texts(list(input))

    @staticmethod
    def name() -> str:
        return "ollama_embedding_function"

    def get_config(self) -> dict[str, Any]:
        model = getattr(self.client, "model", "nomic-embed-text")
        base_url = getattr(self.client, "base_url", "http://127.0.0.1:11434")
        return {"model": model, "url": base_url}

    @classmethod
    def build_from_config(cls, config: dict[str, Any]) -> "_OllamaChromaEmbeddingFunction":
        cfg = Settings(
            embedding_model=config.get("model", "nomic-embed-text"),
            ollama_url=config.get("url", "http://127.0.0.1:11434"),
        )
        return cls(OllamaEmbeddingClient(cfg=cfg))


class ChromaVectorStore:
    def __init__(
        self,
        cfg: Settings = default_settings,
        embedding_client: OllamaEmbeddingClient | None = None,
        persist_dir: str | Path | None = None,
    ):
        self.cfg = cfg
        self.embedding_client = embedding_client or OllamaEmbeddingClient(cfg)
        self.embedding_fn = _OllamaChromaEmbeddingFunction(self.embedding_client)
        self.persist_path = Path(persist_dir or cfg.chroma_persist_dir).resolve()
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_path),
            settings=ChromaSettings(anonymized_telemetry=False, is_persistent=True),
        )
        self.collection_name = cfg.chroma_collection
        self._init_collection()

    def _init_collection(self) -> None:
        try:
            # Check existing metadata if collection exists
            existing = None
            with contextlib.suppress(Exception):
                existing = self.client.get_collection(name=self.collection_name, embedding_function=self.embedding_fn)

            if existing is not None:
                meta = existing.metadata or {}
                # If embedding model changed, recreate to prevent mixed incompatible dimensions
                if meta.get("embedding_model") and meta.get("embedding_model") != self.cfg.embedding_model:
                    self.client.delete_collection(self.collection_name)
                    existing = None

            if existing is None:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_fn,
                    metadata={"hnsw:space": "cosine", "embedding_model": self.cfg.embedding_model},
                )
            else:
                self.collection = existing
        except Exception as exc:
            raise VectorStoreError(f"Failed to initialize Chroma collection: {exc}") from exc

    def index_chunks(self, doc_id: str, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        # Calculate embeddings through local Ollama adapter
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedding_client.embed_texts(texts)

        ids = [f"{doc_id}:{chunk.chunk_id}" for chunk in chunks]
        metadatas = [
            {"document_id": doc_id, "chunk_id": chunk.chunk_id, "page": chunk.page}
            for chunk in chunks
        ]

        try:
            self.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        except Exception as exc:
            raise VectorStoreError(f"Failed to index chunks into ChromaDB: {exc}") from exc

    def search(self, doc_id: str, query: str, k: int = 15) -> list[tuple[Chunk, float]]:
        cleaned_query = query.strip()
        if not cleaned_query:
            return []
        try:
            # Query embedding generated locally via Ollama
            query_vec = self.embedding_client.embed_query(cleaned_query)
            results = self.collection.query(
                query_embeddings=[query_vec],
                n_results=k,
                where={"document_id": doc_id},
            )
        except Exception as exc:
            raise VectorStoreError(f"Vector search failed: {exc}") from exc

        hits: list[tuple[Chunk, float]] = []
        ids_list = results.get("ids", [[]])[0]
        docs_list = results.get("documents", [[]])[0]
        metas_list = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0] if "distances" in results and results["distances"] else []

        for idx, chunk_full_id in enumerate(ids_list):
            doc_text = docs_list[idx]
            meta = metas_list[idx] or {}
            # Cosine distance to similarity: 1 - dist
            dist = distances[idx] if idx < len(distances) else 1.0
            similarity = max(0.0, 1.0 - dist)
            chunk = Chunk(
                chunk_id=meta.get("chunk_id", chunk_full_id.split(":", 1)[-1]),
                page=meta.get("page", 1),
                text=doc_text,
            )
            hits.append((chunk, similarity))

        return hits

    def delete_document(self, doc_id: str) -> None:
        try:
            self.collection.delete(where={"document_id": doc_id})
        except Exception as exc:
            raise VectorStoreError(f"Failed to delete document vectors for {doc_id}: {exc}") from exc

    def clear(self) -> None:
        try:
            self.client.delete_collection(self.collection_name)
            self._init_collection()
        except Exception as exc:
            raise VectorStoreError(f"Failed to clear collection: {exc}") from exc
