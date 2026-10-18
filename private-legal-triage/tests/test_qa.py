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


def test_multi_passage_evidence_and_chunk_ids(parts):
    retriever, index = parts
    client = reply(
        evidence_quotes=[
            "The Tenant shall pay monthly rent of Rs. 25,000",
            "giving 60 days' written notice",
        ]
    )
    answer = answer_question("What are the rent and termination terms?", retriever, index, client)
    assert answer.answerable
    assert len(answer.evidence) == 2
    assert all(e.verification_status == "verified" for e in answer.evidence)
    assert answer.evidence[0].page == 1
    assert answer.evidence[1].page == 2
    # Verify chunk_id is populated where matching
    assert answer.evidence[0].chunk_id is not None or answer.evidence[1].chunk_id is not None


def test_ungrounded_figures_in_answer_detected(parts):
    retriever, index = parts
    client = reply(
        answer="Notice of 999 days is required to terminate.",
        evidence_quotes=["giving 60 days' written notice"],
    )
    answer = answer_question("How much notice must the tenant give?", retriever, index, client)
    assert answer.answerable
    assert "999" in answer.ungrounded_figures
    assert any("do not appear in the document" in note for note in answer.notes)


def test_stemming_matches_morphological_variants(parts):
    retriever, _ = parts
    # Question uses 'terminating' and 'notices', document has 'terminate' and 'notice'
    hits = retriever.search("terminating agreements with notices", 2)
    assert len(hits) > 0
    assert any("TERMINATION" in c.text or "notice" in c.text.lower() for c, _ in hits)


def test_abstention_reason_populated_when_unanswerable(parts):
    retriever, index = parts
    client = reply(answerable=False, answer="")
    answer = answer_question("What is the governing law?", retriever, index, client)
    assert not answer.answerable
    assert answer.abstention_reason is not None
    assert len(answer.limitations) > 0

