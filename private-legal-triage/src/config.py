import os
from dataclasses import dataclass

# Models the user may choose between. Identifiers are Ollama tags. Anything else is rejected.
# Never accept a model name or URL from a client that is not in this mapping.
SUPPORTED_MODELS: dict[str, str] = {
    "gemma3n:e2b": "Gemma 3n E2B",
    "gemma3n:e4b": "Gemma 3n E4B",
}

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
}


@dataclass(frozen=True)
class Settings:
    model: str = os.getenv("TRIAGE_MODEL", "gemma3n:e2b")
    ollama_url: str = os.getenv("TRIAGE_OLLAMA_URL", "http://127.0.0.1:11434")
    request_timeout: float = float(os.getenv("TRIAGE_TIMEOUT", "300"))
    num_ctx: int = int(os.getenv("TRIAGE_NUM_CTX", "8192"))
    ocr_enabled: bool = os.getenv("TRIAGE_OCR_ENABLED", "1").lower() in ("1", "true", "yes")
    enable_encryption_at_rest: bool = os.getenv("TRIAGE_ENCRYPT_AT_REST", "0").lower() in ("1", "true", "yes")
    chunk_max_chars: int = 2400
    chunk_overlap_chars: int = 200
    min_chars_per_page: int = 40
    min_total_chars: int = 200
    min_quote_chars: int = 20
    max_findings_per_chunk: int = 6
    retrieval_top_k: int = 4
    max_pdf_pages: int = 300
    max_file_bytes: int = 50 * 1024 * 1024
    summary_input_limit: int = 6000
    model_retries: int = 1
    max_chunks: int = 1200
    max_documents: int = 20
    max_question_chars: int = 1000
    embedding_model: str = os.getenv("TRIAGE_EMBEDDING_MODEL", "nomic-embed-text")
    chroma_persist_dir: str = os.getenv("TRIAGE_CHROMA_PATH", "./data/chroma")
    chroma_collection: str = os.getenv("TRIAGE_CHROMA_COLLECTION", "zerolatency_chunks_v1")
    hybrid_retrieval_enabled: bool = os.getenv("TRIAGE_HYBRID_RETRIEVAL", "1").lower() in ("1", "true", "yes")
    hybrid_bm25_candidates: int = int(os.getenv("TRIAGE_HYBRID_BM25_K", "15"))
    hybrid_vector_candidates: int = int(os.getenv("TRIAGE_HYBRID_VECTOR_K", "15"))
    hybrid_final_top_k: int = int(os.getenv("TRIAGE_HYBRID_TOP_K", "4"))
    hybrid_rrf_k: int = int(os.getenv("TRIAGE_HYBRID_RRF_K", "60"))


DISCLAIMER = (
    "This tool gives a preliminary, informational reading of a document. It is not a lawyer, "
    "does not give legal advice, and cannot decide whether anything is valid or enforceable. "
    "Matching a quotation to the source shows the text exists; it does not prove the "
    "interpretation is correct. Consult a qualified legal professional before any "
    "consequential decision."
)

ESCALATION = (
    "Please take this clause to a qualified lawyer or a legal aid service in your jurisdiction "
    "and ask them to confirm how it applies to you."
)

SILENT_ANSWER = (
    "The document does not appear to address this question. Nothing in the extracted text "
    "supports an answer, so none is given."
)

VERDICT_NOTICE = (
    "This tool cannot determine whether anything is legally valid, lawful or enforceable. "
    "What follows is only what the document's text says."
)

settings = Settings()
