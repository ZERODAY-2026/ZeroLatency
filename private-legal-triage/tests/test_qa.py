import json

import pytest

from src.chunker import chunk_pages
from src.citation_validator import SourceIndex
from src.document_parser import extract_pages
from src.errors import EmptyQuestion
from src.qa import BM25Index, answer_question, is_verdict_question
from tests.conftest import FakeClient


@pytest.fixture
def parts(rental_pdf):
    pages = extract_pages(rental_pdf)
    chunks = chunk_pages(pages)
    return BM25Index(chunks), SourceIndex(pages)


def reply(**kw):
    base = {
        "answerable": True,
        "answer": "Notice of 60 days is required.",
        "evidence_quotes": [],
        "statement_type": "explicit",
        "jurisdiction_dependent": False,
    }
    base.update(kw)
    return FakeClient([json.dumps(base)])


def test_bm25_ranks_relevant_chunk_first(parts):
    retriever, _ = parts
    top = retriever.search("security deposit refund", 1)[0][0]
    assert "SECURITY DEPOSIT" in top.text


def test_silent_question_never_calls_model(parts):
    retriever, index = parts
    client = reply()
    answer = answer_question("Is a pet elephant allowed on the balcony?", retriever, index, client)
    assert not answer.answerable
    assert client.calls == []
    assert answer.escalation


def test_verified_answer_has_evidence(parts):
    retriever, index = parts
    client = reply(evidence_quotes=["giving 60 days' written notice"])
    answer = answer_question("How much notice must the tenant give to terminate?", retriever, index, client)
    assert answer.answerable
    assert answer.evidence[0].verification_status == "verified"
    assert answer.evidence[0].page == 2


def test_fabricated_evidence_becomes_unanswerable(parts):
    retriever, index = parts
    client = reply(evidence_quotes=["The Tenant may keep pets without any fee at all."])
    answer = answer_question("How much notice must the tenant give to terminate?", retriever, index, client)
    assert not answer.answerable
    assert "no supporting quotation" in answer.notes[0]


def test_model_saying_unanswerable_is_respected(parts):
    retriever, index = parts
    client = reply(answerable=False, answer="Maybe yes, in general law.")
    answer = answer_question("What is the notice for termination?", retriever, index, client)
    assert not answer.answerable
    assert "general law" not in answer.answer


def test_verdict_question_is_declined_but_grounded(parts):
    retriever, index = parts
    assert is_verdict_question("Is the auto-renewal clause enforceable?")
    client = reply(evidence_quotes=["renews automatically for a further eleven months"])
    answer = answer_question("Is the auto-renewal clause enforceable?", retriever, index, client)
    assert answer.verdict_declined
    assert "cannot determine" in answer.answer
    assert answer.escalation
    assert "Do not give one" in client.calls[0][1]


def test_non_verdict_question_not_flagged():
    assert not is_verdict_question("What is the notice period?")


def test_empty_question(parts):
    retriever, index = parts
    with pytest.raises(EmptyQuestion):
        answer_question("   ", retriever, index, reply())
