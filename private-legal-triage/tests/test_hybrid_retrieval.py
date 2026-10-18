import tempfile
from unittest.mock import MagicMock

import pytest

from src.config import Settings
from src.embedding_client import OllamaEmbeddingClient
from src.retrieval import HybridRetriever, RetrievalError, reciprocal_rank_fusion
from src.schemas import Chunk
from src.service import DocumentStore
from src.vector_store import ChromaVectorStore


@pytest.fixture
def sample_chunks():
    return [
        Chunk(
            chunk_id="c1",
            page=1,
            text="The Employee shall receive a gross monthly salary of Rs. 60,000, payable on the last working day.",
        ),
        Chunk(
            chunk_id="c2",
            page=1,
            text="The first six months form a probation period. Either party may end employment with 7 days written notice.",
        ),
        Chunk(
            chunk_id="c3",
            page=2,
            text="After probation, the Employee may resign by giving 45 days written notice. Company may terminate for misconduct without notice.",
        ),
        Chunk(
            chunk_id="c4",
            page=2,
            text="For 12 months after termination, Employee shall not work for direct competitors within the city of Sampletown.",
        ),
    ]


@pytest.fixture
def mock_embed_client():
    client = MagicMock(spec=OllamaEmbeddingClient)
    # Return deterministic 4-dimensional synthetic embeddings based on simple word presence
    def embed_texts(texts):
        res = []
        for t in texts:
            vec = [
                1.0 if "salary" in t.lower() or "pay" in t.lower() else 0.05,
                1.0 if "probation" in t.lower() or "notice" in t.lower() else 0.05,
                1.0 if "resign" in t.lower() or "terminate" in t.lower() else 0.05,
                1.0 if "competitor" in t.lower() or "non-compete" in t.lower() else 0.05,
            ]
            res.append(vec)
        return res

    def embed_query(query):
        return embed_texts([query])[0]

    client.embed_texts.side_effect = embed_texts
    client.embed_query.side_effect = embed_query
    return client


@pytest.fixture
def temp_vector_store(mock_embed_client):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        cfg = Settings(chroma_persist_dir=tmpdir, chroma_collection="test_collection_retrieval")
        store = ChromaVectorStore(cfg=cfg, embedding_client=mock_embed_client, persist_dir=tmpdir)
        yield store


def test_chroma_local_persistence_and_metadata(temp_vector_store, sample_chunks):
    doc_id = "doc_test_1"
    temp_vector_store.index_chunks(doc_id, sample_chunks)

    # Search for salary
    hits = temp_vector_store.search(doc_id, "monthly compensation and salary", k=2)
    assert len(hits) > 0
    top_chunk, score = hits[0]
    assert top_chunk.chunk_id == "c1"
    assert "Rs. 60,000" in top_chunk.text
    assert top_chunk.page == 1
    assert score > 0.5


def test_document_isolation_in_vector_store(temp_vector_store, sample_chunks):
    """Ensure doc_a queries never return chunks belonging to doc_b."""
    temp_vector_store.index_chunks("doc_a", [sample_chunks[0]])
    temp_vector_store.index_chunks("doc_b", [sample_chunks[3]])

    # Query doc_a for competitor non-compete (which only exists in doc_b)
    hits_a = temp_vector_store.search("doc_a", "competitors and non-compete", k=5)
    # Must NOT return doc_b's chunk
    for chunk, _ in hits_a:
        assert chunk.chunk_id != "c4"

    # Query doc_b for salary (which only exists in doc_a)
    hits_b = temp_vector_store.search("doc_b", "monthly salary", k=5)
    for chunk, _ in hits_b:
        assert chunk.chunk_id != "c1"


def test_reciprocal_rank_fusion_logic(sample_chunks):
    # BM25 ranks c1 top, c2 second
    bm25_hits = [(sample_chunks[0], 2.5), (sample_chunks[1], 1.2)]
    # Vector ranks c2 top, c1 second
    vector_hits = [(sample_chunks[1], 0.95), (sample_chunks[0], 0.85)]

    fused = reciprocal_rank_fusion(bm25_hits, vector_hits, rrf_k=60, top_k=2)
    assert len(fused) == 2
    # Both c1 and c2 are in top positions
    chunk_ids = [c.chunk_id for c, _ in fused]
    assert set(chunk_ids) == {"c1", "c2"}
    # Scores must be strictly positive floats
    assert fused[0][1] > 0.0


def test_semantic_paraphrase_retrieval(temp_vector_store, sample_chunks):
    """Vector search handles phrasing that BM25 tokens miss."""
    temp_vector_store.index_chunks("doc_semantic", sample_chunks)
    # Query with semantic concept "rival firms restriction" which matches competitor non-compete
    hits = temp_vector_store.search("doc_semantic", "rival firms and competitor", k=2)
    assert hits
    assert hits[0][0].chunk_id == "c4"


def test_reindex_and_deletion_removes_stale_vectors(temp_vector_store, sample_chunks):
    doc_id = "doc_to_delete"
    temp_vector_store.index_chunks(doc_id, sample_chunks)
    assert len(temp_vector_store.search(doc_id, "salary", k=5)) > 0

    # Delete
    temp_vector_store.delete_document(doc_id)
    assert len(temp_vector_store.search(doc_id, "salary", k=5)) == 0


def test_degraded_retrieval_modes(sample_chunks, mock_embed_client, temp_vector_store):
    doc_id = "doc_degraded"
    temp_vector_store.index_chunks(doc_id, sample_chunks)

    # 1. Normal hybrid
    retriever = HybridRetriever(doc_id, sample_chunks, vector_store=temp_vector_store)
    res_hybrid = retriever.search_hybrid("notice period to resign", k=2)
    assert not res_hybrid.degraded
    assert res_hybrid.mode == "hybrid"
    assert len(res_hybrid.hits) <= 2

    # 2. Vector failure fallback to BM25
    broken_vector_store = MagicMock(spec=ChromaVectorStore)
    broken_vector_store.search.side_effect = Exception("Chroma connection error")
    retriever_fallback = HybridRetriever(doc_id, sample_chunks, vector_store=broken_vector_store)

    res_fallback = retriever_fallback.search_hybrid("resignation notice", k=2)
    assert res_fallback.degraded
    assert len(res_fallback.hits) > 0  # BM25 provided the hits
    assert any("Vector retrieval degraded" in d for d in res_fallback.diagnostics)

    # 3. BM25-only explicit mode
    res_bm25 = retriever.search_hybrid("probation", k=2, mode="bm25")
    assert res_bm25.mode == "bm25"
    assert len(res_bm25.hits) > 0

    # 4. Vector-only explicit mode
    res_vec = retriever.search_hybrid("salary", k=2, mode="vector")
    assert res_vec.mode == "vector"
    assert len(res_vec.hits) > 0

    # 5. Both failed raises RetrievalError
    retriever_fallback.bm25.search = MagicMock(side_effect=Exception("BM25 failure"))
    with pytest.raises(RetrievalError):
        retriever_fallback.search_hybrid("anything", k=2)


def test_document_store_lifecycle_with_hybrid_retriever(tmp_path):
    text_content = (
        "EMPLOYMENT AGREEMENT (SYNTHETIC TEST FIXTURE)\n\n"
        "1. POSITION AND PAY\n"
        "The Employee will work as a Junior Analyst. The Employee shall receive a gross monthly "
        "salary of Rs. 50,000, payable on the last working day of each calendar month. This amount "
        "shall be subject to applicable income tax deductions and provident fund contributions as "
        "required by the laws of India.\n\n"
        "2. TERMINATION AND NOTICE\n"
        "After the probation period of six months, the Employee may resign by giving 30 days "
        "written notice to the Company. The Company may terminate the employment for gross "
        "misconduct without notice. Severance pay shall be calculated based on years of service.\n\n"
        "3. NON-COMPETE\n"
        "For 12 months after leaving the Company, the Employee shall not work for a direct "
        "competitor within the city limits of Sampletown as defined by the municipal boundary."
    )

    cfg = Settings(
        hybrid_retrieval_enabled=True,
        chroma_persist_dir=str(tmp_path / "chroma"),
    )
    store = DocumentStore(cfg=cfg)
    try:
        doc_info = store.upload("contract.txt", text_content.encode("utf-8"))
        assert doc_info.id

        # Search via DocumentStore using hybrid retrieval
        hits = store.search(doc_info.id, "monthly compensation", k=2)
        assert len(hits) > 0

        # Delete document cleans up vector store
        store.delete(doc_info.id)
        assert doc_info.id not in store._docs
    finally:
        store.close()
