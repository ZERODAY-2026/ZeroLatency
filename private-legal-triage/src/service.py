"""Framework-neutral application service.

The HTTP API (src/api.py) and any other front end call this layer. It owns documents, jobs and
cleanup, and delegates all analysis to DocumentSession, so analysis logic exists in one place.
"""

import contextlib
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel

from .config import Settings
from .config import settings as default_settings
from .errors import (
    AnalysisCancelled,
    Busy,
    DocumentNotFound,
    EmptyQuestion,
    LimitExceeded,
    TriageError,
    UnreadableDocument,
    UnsupportedFormat,
)
from .gemma_client import ChatClient, OllamaClient
from .highlight import render_page
from .models import ModelsStatus, models_status, validate_model
from .pipeline import DocumentSession
from .privacy import PrivateWorkspace, network_guard
from .schemas import Answer, TriageResult

ALLOWED_SUFFIXES = {".pdf", ".txt"}


class DocumentInfo(BaseModel):
    id: str
    name: str
    size_bytes: int
    pages: int
    chunks: int
    created_at: float
    analyzed: bool = False


class PassageHit(BaseModel):
    chunk_id: str
    page: int
    score: float
    text: str


class PageContent(BaseModel):
    document_id: str
    page: int
    text: str


class JobStatus(BaseModel):
    id: str
    document_id: str
    model: str | None
    state: str  # queued | running | completed | failed | cancelled
    stage: str  # waiting | analysing_sections | summarising_and_verifying | done
    sections_done: int = 0
    sections_total: int = 0
    error_code: str | None = None
    error_message: str | None = None
    result: TriageResult | None = None


@dataclass
class _Job:
    id: str
    document_id: str
    model: str | None
    state: str = "queued"
    stage: str = "waiting"
    done: int = 0
    total: int = 0
    error: tuple[str, str] | None = None
    result: TriageResult | None = None
    cancel: threading.Event = field(default_factory=threading.Event)
    thread: threading.Thread | None = None


@dataclass
class _Doc:
    info: DocumentInfo
    path: Path
    session: DocumentSession


class DocumentStore:
    def __init__(
        self,
        cfg: Settings = default_settings,
        client: ChatClient | None = None,
        workspace: PrivateWorkspace | None = None,
    ):
        self.cfg = cfg
        self.client = client or OllamaClient(cfg)
        self._workspace = workspace or PrivateWorkspace()
        self._workspace.__enter__()
        self._docs: dict[str, _Doc] = {}
        self._jobs: dict[str, _Job] = {}
        self._lock = threading.RLock()
        self._model_gate = threading.Lock()  # one local-model task at a time

    # ---- documents ----------------------------------------------------------------
    def upload(self, filename: str, data: bytes) -> DocumentInfo:
        suffix = Path(filename or "").suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise UnsupportedFormat("Only PDF and plain text (.txt) files are supported.")
        if not data:
            raise UnreadableDocument("The uploaded file is empty.")
        if len(data) > self.cfg.max_file_bytes:
            raise LimitExceeded("The file is larger than the supported size limit.")
        with self._lock:
            if len(self._docs) >= self.cfg.max_documents:
                raise LimitExceeded("Too many documents are open. Delete one before uploading another.")
        path = self._workspace.save_upload(filename, data)
        try:
            session = DocumentSession(path, self.client, self.cfg)
        except BaseException:
            self._workspace.delete_file(path)
            raise
        doc_id = uuid.uuid4().hex
        info = DocumentInfo(
            id=doc_id,
            name=Path(filename).name,
            size_bytes=len(data),
            pages=len(session.pages),
            chunks=len(session.chunks),
            created_at=time.time(),
        )
        with self._lock:
            self._docs[doc_id] = _Doc(info, path, session)
        return info

    def list_documents(self) -> list[DocumentInfo]:
        with self._lock:
            return [doc.info for doc in self._docs.values()]

    def get(self, doc_id: str) -> DocumentInfo:
        return self._doc(doc_id).info

    def delete(self, doc_id: str) -> None:
        with self._lock:
            doc = self._docs.pop(doc_id, None)
            if doc is None:
                raise DocumentNotFound("No such document.")
            jobs = [job for job in self._jobs.values() if job.document_id == doc_id]
            for job in jobs:
                job.cancel.set()
        for job in jobs:
            if job.thread is not None:
                job.thread.join(timeout=30)
        with self._lock:
            for job in jobs:
                self._jobs.pop(job.id, None)
        self._workspace.delete_file(doc.path)
        doc.session.result = None
        doc.session.chunks.clear()
        doc.session.pages.clear()
        doc.session.retriever = None  # type: ignore[assignment]
        doc.session.index = None  # type: ignore[assignment]

    def close(self) -> None:
        with self._lock:
            ids = list(self._docs)
        for doc_id in ids:
            with contextlib.suppress(DocumentNotFound):
                self.delete(doc_id)
        self._workspace.cleanup()

    # ---- retrieval and source passages ---------------------------------------------
    def search(self, doc_id: str, query: str, k: int = 4) -> list[PassageHit]:
        if not query.strip():
            raise EmptyQuestion("Please enter a search query.")
        hits = self._doc(doc_id).session.retriever.search(query, max(1, min(k, 20)))
        return [PassageHit(chunk_id=c.chunk_id, page=c.page, score=round(s, 4), text=c.text) for c, s in hits]

    def page(self, doc_id: str, number: int) -> PageContent:
        doc = self._doc(doc_id)
        for page in doc.session.pages:
            if page.number == number:
                return PageContent(document_id=doc_id, page=number, text=page.text)
        raise DocumentNotFound("No such page.")

    def page_image(self, doc_id: str, number: int, quote: str | None = None) -> bytes:
        doc = self._doc(doc_id)
        return render_page(doc.path, number, quote)

    # ---- models ---------------------------------------------------------------------
    def models(self) -> ModelsStatus:
        return models_status(self.client, getattr(self.client, "model", self.cfg.model))

    # ---- analysis jobs --------------------------------------------------------------
    def start_analysis(self, doc_id: str, model: str | None = None) -> JobStatus:
        doc = self._doc(doc_id)
        if model is not None:
            validate_model(model)
        if not self._model_gate.acquire(blocking=False):
            raise Busy("Another analysis or question is already running. Try again when it finishes.")
        job = _Job(id=uuid.uuid4().hex, document_id=doc_id, model=model)
        with self._lock:
            self._jobs[job.id] = job
        job.thread = threading.Thread(target=self._run, args=(job, doc), daemon=True)
        job.thread.start()
        return self._status(job)

    def _run(self, job: _Job, doc: _Doc) -> None:
        try:
            job.state, job.stage = "running", "analysing_sections"

            def progress(done: int, total: int) -> None:
                job.done, job.total = done, total
                if done == total:
                    job.stage = "summarising_and_verifying"

            with network_guard():
                result = doc.session.analyze(progress, model=job.model, should_cancel=job.cancel.is_set)
            job.result = result
            job.state, job.stage = "completed", "done"
            doc.info.analyzed = True
        except AnalysisCancelled:
            job.state, job.stage = "cancelled", "done"
        except TriageError as error:
            job.state, job.stage = "failed", "done"
            job.error = (type(error).__name__, str(error))
        except Exception:
            job.state, job.stage = "failed", "done"
            job.error = ("InternalError", "The analysis failed unexpectedly. No document content was logged.")
        finally:
            self._model_gate.release()

    def job(self, job_id: str) -> JobStatus:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise DocumentNotFound("No such job.")
        return self._status(job)

    def cancel(self, job_id: str) -> JobStatus:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise DocumentNotFound("No such job.")
        job.cancel.set()  # takes effect after the section currently being processed
        return self._status(job)

    def wait(self, job_id: str, timeout: float = 60.0) -> JobStatus:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise DocumentNotFound("No such job.")
        if job.thread is not None:
            job.thread.join(timeout)
        return self._status(job)

    def result(self, doc_id: str) -> TriageResult:
        result = self._doc(doc_id).session.result
        if result is None:
            raise DocumentNotFound("This document has not been analysed yet.")
        return result

    def ask(self, doc_id: str, question: str, model: str | None = None) -> Answer:
        doc = self._doc(doc_id)
        if len(question) > self.cfg.max_question_chars:
            raise LimitExceeded(f"Questions are limited to {self.cfg.max_question_chars} characters.")
        if model is not None:
            validate_model(model)
        if not self._model_gate.acquire(blocking=False):
            raise Busy("Another analysis or question is already running. Try again when it finishes.")
        try:
            with network_guard():
                return doc.session.ask(question, model=model)
        finally:
            self._model_gate.release()

    # ---- internals ------------------------------------------------------------------
    def _doc(self, doc_id: str) -> _Doc:
        with self._lock:
            doc = self._docs.get(doc_id)
        if doc is None:
            raise DocumentNotFound("No such document.")
        return doc

    @staticmethod
    def _status(job: _Job) -> JobStatus:
        return JobStatus(
            id=job.id,
            document_id=job.document_id,
            model=job.model,
            state=job.state,
            stage=job.stage,
            sections_done=job.done,
            sections_total=job.total,
            error_code=job.error[0] if job.error else None,
            error_message=job.error[1] if job.error else None,
            result=job.result,
        )

