from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["deadline", "obligation", "right", "penalty", "termination", "risk", "ambiguity", "other"]
StatementType = Literal["explicit", "interpretation"]
Confidence = Literal["low", "medium", "high"]
Verification = Literal["verified", "unverified"]


class Page(BaseModel):
    number: int
    text: str
    is_ocr: bool = False


class Chunk(BaseModel):
    chunk_id: str
    page: int
    text: str


class ModelFinding(BaseModel):
    category: Category
    title: str
    explanation: str
    evidence_quote: str
    statement_type: StatementType
    jurisdiction_dependent: bool = False


class ChunkAnalysis(BaseModel):
    chunk_summary: str
    findings: list[ModelFinding] = Field(default_factory=list)


class SummaryOut(BaseModel):
    summary: str


class Candidate(ModelFinding):
    page: int
    chunk_id: str


class AnalysisDraft(BaseModel):
    summary: str
    candidates: list[Candidate]
    failed_chunks: list[str] = Field(default_factory=list)


class Finding(Candidate):
    verification_status: Verification
    verification_note: str
    confidence: Confidence
    needs_human_review: bool
    ungrounded_figures: list[str] = Field(default_factory=list)


class KeyFact(BaseModel):
    label: str
    value: str
    page: int
    snippet: str
    normalized_value: str | float | int | None = None
    fact_subtype: str | None = None
    conflicting: bool = False


class ChecklistItem(BaseModel):
    topic: str
    found: bool
    pages: list[int] = Field(default_factory=list)


class TriageResult(BaseModel):
    source_name: str
    model: str
    summary: str
    findings: list[Finding]
    key_facts: list[KeyFact]
    checklist: list[ChecklistItem]
    conflicts: list[dict] = Field(default_factory=list)
    unusual_clauses: list[dict] = Field(default_factory=list)
    limitations: list[str]
    disclaimer: str
    pages_analyzed: int
    chunks_analyzed: int
    elapsed_seconds: float


class ModelAnswer(BaseModel):
    answerable: bool
    answer: str
    evidence_quotes: list[str] = Field(
        description="Exact quotes copied verbatim from the document passage that support the answer. If unanswerable, provide an empty list []."
    )
    statement_type: StatementType = "explicit"
    jurisdiction_dependent: bool = False


class Evidence(BaseModel):
    quote: str
    page: int | None
    chunk_id: str | None = None
    verification_status: Verification


class Answer(BaseModel):
    question: str
    answerable: bool
    answer: str
    evidence: list[Evidence] = Field(default_factory=list)
    statement_type: StatementType = "explicit"
    jurisdiction_dependent: bool = False
    verdict_declined: bool = False
    escalation: str | None = None
    notes: list[str] = Field(default_factory=list)
    ungrounded_figures: list[str] = Field(default_factory=list)
    model: str | None = None
    language: str = "en"
    abstention_reason: str | None = None
    limitations: list[str] = Field(default_factory=list)
