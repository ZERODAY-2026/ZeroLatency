from collections import defaultdict
from dataclasses import dataclass, field
from typing import Literal

from .config import Settings
from .config import settings as default_settings
from .errors import TriageError
from .qa import BM25Index
from .schemas import Chunk
from .vector_store import ChromaVectorStore


class RetrievalError(TriageError):
    """Raised when all retrieval sources fail."""


@dataclass
class HybridSearchResult:
    hits: list[tuple[Chunk, float]]
    mode: str = "hybrid"
    degraded: bool = False
    diagnostics: list[str] = field(default_factory=list)


def reciprocal_rank_fusion(
    bm25_hits: list[tuple[Chunk, float]],
    vector_hits: list[tuple[Chunk, float]],
    rrf_k: int = 60,
    top_k: int = 4,
) -> list[tuple[Chunk, float]]:
    """Compute Reciprocal Rank Fusion (RRF) across BM25 and vector candidate lists.

    RRF_score(doc) = sum(1.0 / (rrf_k + rank)) for each rank list (1-indexed).
    Preserves exact chunk metadata and source text.
    """
    scores: dict[str, float] = defaultdict(float)
    chunk_map: dict[str, Chunk] = {}

    # RRF over BM25 ranks
    for rank, (chunk, _) in enumerate(bm25_hits, start=1):
        scores[chunk.chunk_id] += 1.0 / (rrf_k + rank)
        chunk_map[chunk.chunk_id] = chunk

    # RRF over Vector ranks
    for rank, (chunk, _) in enumerate(vector_hits, start=1):
        scores[chunk.chunk_id] += 1.0 / (rrf_k + rank)
        chunk_map[chunk.chunk_id] = chunk

    sorted_chunk_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)
    return [(chunk_map[cid], round(scores[cid], 6)) for cid in sorted_chunk_ids[:top_k]]


class HybridRetriever:
    """Combines BM25 keyword retrieval and ChromaDB local vector storage."""

    def __init__(
        self,
        doc_id: str,
        chunks: list[Chunk],
        vector_store: ChromaVectorStore | None = None,
        cfg: Settings = default_settings,
    ):
        self.doc_id = doc_id
        self.chunks = chunks
        self.bm25 = BM25Index(chunks)
        self.vector_store = vector_store
        self.cfg = cfg

    def search(
        self,
        query: str,
        k: int | None = None,
        mode: Literal["hybrid", "bm25", "vector"] | None = None,
    ) -> list[tuple[Chunk, float]]:
        """Drop-in compatible with BM25Index.search(query, k). Returns list[tuple[Chunk, float]]."""
        result = self.search_hybrid(query, k=k, mode=mode)
        return result.hits

    def search_hybrid(
        self,
        query: str,
        k: int | None = None,
        mode: Literal["hybrid", "bm25", "vector"] | None = None,
    ) -> HybridSearchResult:
        cleaned_query = query.strip()
        if not cleaned_query:
            return HybridSearchResult(hits=[], mode=mode or "hybrid")

        retrieval_mode = mode or ("hybrid" if self.cfg.hybrid_retrieval_enabled else "bm25")
        final_top_k = k or self.cfg.hybrid_final_top_k
        bm25_candidates = self.cfg.hybrid_bm25_candidates
        vector_candidates = self.cfg.hybrid_vector_candidates
        rrf_k = self.cfg.hybrid_rrf_k

        diagnostics: list[str] = []
        bm25_hits: list[tuple[Chunk, float]] = []
        vector_hits: list[tuple[Chunk, float]] = []

        bm25_failed = False
        vector_failed = False

        # 1. BM25 Search
        if retrieval_mode in ("hybrid", "bm25"):
            try:
                bm25_hits = self.bm25.search(cleaned_query, bm25_candidates)
            except Exception as exc:
                bm25_failed = True
                diagnostics.append(f"BM25 retrieval encountered an issue: {exc}")

        # 2. Vector Search
        if retrieval_mode in ("hybrid", "vector"):
            if self.vector_store is None:
                vector_failed = True
                diagnostics.append("Vector store is not configured or unavailable.")
            else:
                try:
                    vector_hits = self.vector_store.search(
                        doc_id=self.doc_id,
                        query=cleaned_query,
                        k=vector_candidates,
                    )
                except Exception as exc:
                    vector_failed = True
                    diagnostics.append(f"Vector retrieval degraded: {exc}")

        # Handling retrieval modes and degraded state
        if retrieval_mode == "bm25":
            if bm25_failed:
                raise RetrievalError(f"BM25 retrieval failed: {'; '.join(diagnostics)}")
            return HybridSearchResult(hits=bm25_hits[:final_top_k], mode="bm25")

        if retrieval_mode == "vector":
            if vector_failed:
                raise RetrievalError(f"Vector retrieval failed: {'; '.join(diagnostics)}")
            return HybridSearchResult(hits=vector_hits[:final_top_k], mode="vector")

        # Hybrid mode
        if bm25_failed and vector_failed:
            raise RetrievalError(f"All retrieval systems failed: {'; '.join(diagnostics)}")

        if vector_failed and not bm25_failed:
            return HybridSearchResult(
                hits=bm25_hits[:final_top_k],
                mode="hybrid",
                degraded=True,
                diagnostics=diagnostics,
            )

        if bm25_failed and not vector_failed:
            return HybridSearchResult(
                hits=vector_hits[:final_top_k],
                mode="hybrid",
                degraded=True,
                diagnostics=diagnostics,
            )

        # Normal hybrid with RRF
        fused = reciprocal_rank_fusion(bm25_hits, vector_hits, rrf_k=rrf_k, top_k=final_top_k)
        return HybridSearchResult(
            hits=fused,
            mode="hybrid",
            degraded=False,
            diagnostics=diagnostics,
        )
