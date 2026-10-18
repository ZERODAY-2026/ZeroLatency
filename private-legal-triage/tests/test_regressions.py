"""Regression tests for gaps found while auditing the code against backend.md."""

import contextlib
import json

from src.chunker import chunk_pages
from src.citation_validator import SourceIndex
from src.errors import InvalidModelOutput
from src.gemma_client import StructuredStats, call_structured
from src.qa import BM25Index, answer_question
from src.schemas import Page, SummaryOut
from tests.conftest import FakeClient

PAGES = [Page(number=1, text="2. RENT\nThe Tenant shall pay monthly rent of Rs. 25,000 on or before the 5th day of each month.")]


def ask(answer_text):
    payload = {
        "answerable": True,
        "answer": answer_text,
        "evidence_quotes": ["monthly rent of Rs. 25,000 on or before the 5th day of each month"],
        "statement_type": "explicit",
        "jurisdiction_dependent": False,
    }
    chunks = chunk_pages(PAGES)
    return answer_question("How much is the monthly rent?", BM25Index(chunks), SourceIndex(PAGES), FakeClient([json.dumps(payload)]))


def test_answer_with_invented_figure_is_flagged():
    # Before the fix, QA verified quotes but never checked figures in the answer text.
    answer = ask("The monthly rent is Rs. 30,000.")
    assert answer.answerable and answer.ungrounded_figures == ["30000"]
    assert any("do not appear in the document" in note for note in answer.notes)


def test_answer_with_grounded_figures_is_not_flagged():
    answer = ask("The monthly rent is Rs. 25,000, due by the 5th.")
    assert answer.ungrounded_figures == [] and answer.notes == []


def test_structured_stats_count_first_try_and_retry_and_failure():
    outputs = iter(["bad", '{"summary": "a"}', '{"summary": "b"}', "bad", "bad"])
    client = FakeClient([lambda user: next(outputs)])
    client.stats = StructuredStats()
    call_structured(client, "s", "u", SummaryOut)  # retry succeeds
    call_structured(client, "s", "u", SummaryOut)  # first try succeeds
    with contextlib.suppress(InvalidModelOutput):
        call_structured(client, "s", "u", SummaryOut)
    assert (client.stats.calls, client.stats.valid, client.stats.first_try_valid, client.stats.failed) == (3, 2, 1, 1)
