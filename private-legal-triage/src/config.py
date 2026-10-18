import os
from dataclasses import dataclass

# Models the user may choose between. Identifiers are Ollama tags. Anything else is rejected.
# Never accept a model name or URL from a client that is not in this mapping.
SUPPORTED_MODELS: dict[str, str] = {
    "gemma3n:e2b": "Gemma 3n E2B",
    "gemma3n:e4b": "Gemma 3n E4B",
}


@dataclass(frozen=True)
class Settings:
    model: str = os.getenv("TRIAGE_MODEL", "gemma3n:e2b")
    ollama_url: str = os.getenv("TRIAGE_OLLAMA_URL", "http://127.0.0.1:11434")
    request_timeout: float = float(os.getenv("TRIAGE_TIMEOUT", "300"))
    num_ctx: int = int(os.getenv("TRIAGE_NUM_CTX", "8192"))
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
