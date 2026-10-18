import json

import pytest

from src.errors import DocumentError, UnsupportedFormat
from src.highlight import render_page
from src.pipeline import DocumentSession
from src.privacy import network_guard
from tests.conftest import FakeClient, analysis_json, finding

SUMMARY = json.dumps({"summary": "A short residential lease."})
ANSWER = json.dumps(
    {
        "answerable": True,
        "answer": "The deposit is Rs. 75,000 and refundable.",
        "evidence_quotes": ["refundable security deposit of Rs. 75,000"],
        "statement_type": "explicit",
        "jurisdiction_dependent": False,
    }
)


def scripted(findings_by_marker):
    def respond(user):
        if user.startswith("Section notes"):
            return SUMMARY
        if user.startswith("Question:"):
            return ANSWER
        for marker, items in findings_by_marker.items():
            if marker in user:
                return analysis_json(items)
        return analysis_json()

    return FakeClient([respond])


def test_end_to_end_offline(rental_pdf):
    good = finding("monthly rent of Rs. 25,000 on or before the 5th day of each month")
    fabricated = finding("The landlord must pay the tenant Rs. 1,00,000 annually.", title="Invented")
    termination = finding(
        "The Tenant may terminate this agreement by giving 60 days' written notice.",
        category="termination",
        title="Tenant exit",
        explanation="The tenant needs 60 days notice.",
    )
    client = scripted({"2. RENT": [good, fabricated], "4. TERMINATION": [termination]})
    with network_guard() as blocked:
        session = DocumentSession(rental_pdf, client)
        result = session.analyze()
        answer = session.ask("What is the security deposit?")
    assert blocked == []
    statuses = {f.title: f.verification_status for f in result.findings}
    assert statuses["Monthly rent"] == "verified"
    assert statuses["Tenant exit"] == "verified"
    assert statuses["Invented"] == "unverified"
    assert result.findings[-1].title == "Invented"
    assert any("could not be verified" in note for note in result.limitations)
    assert any("page(s) 2" in note for note in result.limitations)
    assert result.pages_analyzed == 2
    assert result.summary
    assert "not a lawyer" in result.disclaimer
    assert answer.answerable
    assert answer.evidence[0].page == 1
    assert answer.evidence[0].verification_status == "verified"


def test_text_file_pipeline(rental_txt):
    session = DocumentSession(rental_txt, scripted({}))
    result = session.analyze()
    assert result.findings == []
    assert result.key_facts


def test_highlight_renders_png(rental_pdf):
    png = render_page(rental_pdf, 1, "monthly rent of Rs. 25,000")
    assert png.startswith(b"\x89PNG")


def test_highlight_errors(rental_pdf, rental_txt):
    with pytest.raises(DocumentError):
        render_page(rental_pdf, 9)
    with pytest.raises(UnsupportedFormat):
        render_page(rental_txt, 1)
