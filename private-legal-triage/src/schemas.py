from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["deadline", "obligation", "right", "penalty", "termination", "risk", "ambiguity", "other"]
StatementType = Literal["explicit", "interpretation"]
Confidence = Literal["low", "medium", "high"]
Verification = Literal["verified", "unverified"]


class Page(BaseModel):
    number: int
    text: str


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
    limitations: list[str]
    disclaimer: str
    pages_analyzed: int
    chunks_analyzed: int
    elapsed_seconds: float


class ModelAnswer(BaseModel):
    answerable: bool
    answer: str
    evidence_quotes: list[str] = Field(default_factory=list)
    statement_type: StatementType = "explicit"
    jurisdiction_dependent: bool = False


class Evidence(BaseModel):
    quote: str
    page: int | None
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
