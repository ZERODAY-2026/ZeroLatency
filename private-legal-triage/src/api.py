"""Optional FastAPI layer over DocumentStore, for a React (or any HTTP) front end.

Run locally only:  uvicorn src.api:app --host 127.0.0.1 --port 8000
Requires: pip install -r requirements-api.txt
The Streamlit/Python path (DocumentSession directly) is unchanged and does not need this module.
"""

import os
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .comparison import ComparisonResult
from .config import DISCLAIMER, settings
from .errors import (
    AnalysisCancelled,
    Busy,
    DocumentNotFound,
    EmptyQuestion,
    EncryptedDocument,
    InsufficientMemory,
    InvalidModelOutput,
    LimitExceeded,
    ModelMissing,
    ModelTimeout,
    NoExtractableText,
    OllamaUnavailable,
    PrivacyViolation,
    TriageError,
    UnreadableDocument,
    UnsupportedFormat,
    UnsupportedLanguage,
    UnsupportedModel,
)
from .privacy import is_loopback_host, network_guard
from .retrieval import RetrievalError
from .schemas import Answer, TriageResult
from .service import DocumentInfo, DocumentStore, JobStatus, PageContent, PassageHit
from .vector_store import VectorStoreError

DEFAULT_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
)

STATUS_BY_ERROR: dict[type[TriageError], int] = {
    UnsupportedFormat: 415,
    EncryptedDocument: 422,
    UnreadableDocument: 422,
    NoExtractableText: 422,
    LimitExceeded: 413,
    UnsupportedModel: 400,
    UnsupportedLanguage: 400,
    EmptyQuestion: 400,
    DocumentNotFound: 404,
    ModelMissing: 409,
    Busy: 409,
    AnalysisCancelled: 409,
    OllamaUnavailable: 503,
    InsufficientMemory: 507,
    ModelTimeout: 504,
    InvalidModelOutput: 502,
    PrivacyViolation: 403,
    VectorStoreError: 500,
    RetrievalError: 500,
}


def cors_origins() -> list[str]:
    origins = [o.strip() for o in os.getenv("TRIAGE_CORS_ORIGINS", DEFAULT_ORIGINS).split(",") if o.strip()]
    for origin in origins:
        host = urlparse(origin).hostname
        if not host or not is_loopback_host(host):
            raise PrivacyViolation(f"CORS origin must be a loopback address: {origin}")
    return origins


class AnalyzeRequest(BaseModel):
    model: str | None = Field(default=None, description="Explicit model id, e.g. gemma3n:e4b")


class AskRequest(BaseModel):
    question: str
    model: str | None = None
    language: str = Field(default="en", description="Output language code (e.g. en, hi, es, fr, de)")
    retrieval_mode: str | None = Field(default=None, description="Retrieval mode: hybrid | bm25 | vector")


class CompareRequest(BaseModel):
    doc_a: str = Field(description="Document ID for the baseline / older version")
    doc_b: str = Field(description="Document ID for the target / newer version")
    include_formatting: bool = Field(default=False, description="Include purely cosmetic formatting differences")


class SearchRequest(BaseModel):
    query: str
    k: int = Field(default=4, ge=1, le=20)
    mode: str | None = Field(default=None, description="Retrieval mode: hybrid | bm25 | vector")


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def create_app(store: DocumentStore | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.store = store or DocumentStore(settings)
        with network_guard():
            try:
                yield
            finally:
                app.state.store.close()

    app = FastAPI(title="Private Legal Document Triage", version="1.0", lifespan=lifespan)
    if store is not None:
        app.state.store = store
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins(),
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(TriageError)
    async def triage_error_handler(_: Request, error: TriageError) -> JSONResponse:
        status = next((code for cls, code in STATUS_BY_ERROR.items() if isinstance(error, cls)), 500)
        return JSONResponse(status_code=status, content=error_body(type(error).__name__, str(error)))

    @app.exception_handler(Exception)
    async def unexpected_error_handler(_: Request, __: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=error_body("InternalError", "Unexpected error. No document content was logged."),
        )

    def store_of(request: Request) -> DocumentStore:
        return request.app.state.store

    @app.get("/")
    def root(request: Request) -> dict:
        status = store_of(request).models()
        return {
            "name": "ZeroLatency Private Legal Triage API",
            "status": "online",
            "ollama_available": status.ollama_available,
            "docs_url": "/docs",
            "health_url": "/health",
        }

    @app.get("/health")
    def health(request: Request) -> dict:
        status = store_of(request).models()
        return {"status": "ok", "ollama_available": status.ollama_available, "disclaimer": DISCLAIMER}

    @app.get("/models")
    def models(request: Request):
        return store_of(request).models()

    @app.post("/documents", response_model=DocumentInfo, status_code=201)
    def upload(request: Request, file: UploadFile) -> DocumentInfo:
        limit = settings.max_file_bytes
        data = file.file.read(limit + 1)
        return store_of(request).upload(file.filename or "", data)

    @app.get("/documents", response_model=list[DocumentInfo])
    def list_documents(request: Request):
        return store_of(request).list_documents()

    @app.post("/documents/compare", response_model=ComparisonResult)
    def compare(body: CompareRequest, request: Request) -> ComparisonResult:
        return store_of(request).compare(body.doc_a, body.doc_b, body.include_formatting)

    @app.get("/documents/{doc_id}", response_model=DocumentInfo)
    def get_document(doc_id: str, request: Request):
        return store_of(request).get(doc_id)

    @app.delete("/documents/{doc_id}", status_code=204)
    def delete_document(doc_id: str, request: Request) -> Response:
        store_of(request).delete(doc_id)
        return Response(status_code=204)

    @app.post("/documents/{doc_id}/search", response_model=list[PassageHit])
    def search(doc_id: str, body: SearchRequest, request: Request):
        return store_of(request).search(doc_id, body.query, body.k, mode=body.mode)

    @app.get("/documents/{doc_id}/pages/{number}", response_model=PageContent)
    def page(doc_id: str, number: int, request: Request):
        return store_of(request).page(doc_id, number)

    @app.get("/documents/{doc_id}/pages/{number}/image")
    def page_image(doc_id: str, number: int, request: Request, quote: str | None = None) -> Response:
        png = store_of(request).page_image(doc_id, number, quote)
        return Response(content=png, media_type="image/png")

    @app.post("/documents/{doc_id}/analyze", response_model=JobStatus, status_code=202)
    def analyze(doc_id: str, request: Request, body: AnalyzeRequest | None = None):
        return store_of(request).start_analysis(doc_id, body.model if body else None)

    @app.get("/documents/{doc_id}/result", response_model=TriageResult)
    def result(doc_id: str, request: Request):
        return store_of(request).result(doc_id)

    @app.post("/documents/{doc_id}/ask", response_model=Answer)
    def ask(doc_id: str, body: AskRequest, request: Request):
        return store_of(request).ask(doc_id, body.question, body.model, body.language, retrieval_mode=body.retrieval_mode)

    @app.get("/jobs/{job_id}", response_model=JobStatus)
    def job(job_id: str, request: Request):
        return store_of(request).job(job_id)

    @app.post("/jobs/{job_id}/cancel", response_model=JobStatus)
    def cancel(job_id: str, request: Request):
        return store_of(request).cancel(job_id)

    return app


app = create_app()
