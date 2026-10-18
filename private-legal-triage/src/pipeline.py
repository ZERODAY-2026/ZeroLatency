import time
from collections.abc import Callable
from pathlib import Path

from .checklist import scan_checklist
from .chunker import chunk_pages
from .citation_validator import SourceIndex, validate_all
from .config import DISCLAIMER, Settings
from .config import settings as default_settings
from .document_parser import extract_pages, low_text_pages
from .errors import UnreadableDocument
from .facts import extract_key_facts
from .gemma_client import ChatClient, OllamaClient
from .models import validate_model
from .qa import BM25Index, answer_question
from .schemas import Answer, Finding, TriageResult
from .triage import analyze_document, detect_injection_pages


class DocumentSession:
    def __init__(self, path: str | Path, client: ChatClient | None = None, cfg: Settings = default_settings):
        self.path = Path(path)
        self.cfg = cfg
        self.client = client or OllamaClient(cfg)
        self.pages = extract_pages(self.path, cfg)
        self.chunks = chunk_pages(self.pages, cfg)
        if len(self.chunks) > cfg.max_chunks:
            raise UnreadableDocument(
                f"The document is too long to analyse here (more than {cfg.max_chunks} sections)."
            )
        self.index = SourceIndex(self.pages, cfg)
        self.retriever = BM25Index(self.chunks)
        self.result: TriageResult | None = None

    def client_for(self, model: str | None = None) -> ChatClient:
        """Resolve the client for one request. `model=None` means the session's configured model.

        An explicit model is checked against the allowlist, must be installed, and is the only
        model used. Nothing is re-parsed or re-indexed, and there is no fallback to another model.
        """
        if model is None:
            return self.client
        model = validate_model(model)
        prepare = getattr(self.client, "prepare_model", None)
        if prepare:
            prepare(model)
        bind = getattr(self.client, "with_model", None)
        return bind(model) if bind else self.client

    def analyze(
        self,
        on_progress: Callable[[int, int], None] | None = None,
        model: str | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> TriageResult:
        client = self.client_for(model)
        started = time.perf_counter()
        draft = analyze_document(self.chunks, client, self.cfg, on_progress, should_cancel)
        findings = validate_all(draft.candidates, self.index)
        self.result = TriageResult(
            source_name=self.path.name,
            model=getattr(client, "model", self.cfg.model),
            summary=draft.summary,
            findings=findings,
            key_facts=extract_key_facts(self.pages),
            checklist=scan_checklist(self.pages),
            limitations=self._limitations(findings, draft.failed_chunks, bool(draft.summary)),
            disclaimer=DISCLAIMER,
            pages_analyzed=len(self.pages),
            chunks_analyzed=len(self.chunks),
            elapsed_seconds=round(time.perf_counter() - started, 2),
        )
        return self.result

    def ask(self, question: str, model: str | None = None) -> Answer:
        client = self.client_for(model)
        answer = answer_question(question, self.retriever, self.index, client, self.cfg)
        answer.model = getattr(client, "model", self.cfg.model)
        return answer

    def _limitations(self, findings: list[Finding], failed: list[str], has_summary: bool) -> list[str]:
        notes = [
            "Findings are candidates produced by a small local language model and may miss "
            "important issues. The list is not exhaustive.",
            "Checklist entries only show whether related wording appears in the extracted text. "
            "'Not found' is not a legal conclusion.",
        ]
        sparse = low_text_pages(self.pages, self.cfg)
        if sparse:
            notes.append(
                "Pages with little or no extractable text were not analysed (possibly scanned "
                f"images; local OCR is not supported): {', '.join(map(str, sparse))}."
            )
        if failed:
            notes.append(
                f"{len(failed)} section(s) could not be analysed because the model returned unusable output."
            )
        if not has_summary:
            notes.append("A summary could not be generated.")
        unverified = sum(f.verification_status == "unverified" for f in findings)
        if unverified:
            notes.append(f"{unverified} finding(s) have quotations that could not be verified.")
        injected = detect_injection_pages(self.pages)
        if injected:
            notes.append(
                "Text resembling instructions to an AI system appears on page(s) "
                f"{', '.join(map(str, injected))}. It was treated as document content only."
            )
        if any(f.jurisdiction_dependent for f in findings):
            notes.append("Some findings depend on local law that this tool does not assess.")
        return notes
