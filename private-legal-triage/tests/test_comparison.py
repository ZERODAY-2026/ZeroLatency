"""Tests for two-version document comparison."""

from fastapi.testclient import TestClient

from src.api import create_app
from src.comparison import compare_documents
from src.schemas import Page
from src.service import DocumentStore


def test_identical_documents():
    pages_a = [Page(number=1, text="The Tenant shall pay a monthly rent of Rs. 25,000 on or before the 5th day of each month.")]
    pages_b = [Page(number=1, text="The Tenant shall pay a monthly rent of Rs. 25,000 on or before the 5th day of each month.")]

    res = compare_documents("doc1", "Contract_v1.txt", pages_a, "doc2", "Contract_v2.txt", pages_b)
    assert res.total_changes == 0
    assert res.added_count == 0
    assert res.removed_count == 0
    assert res.modified_count == 0
    assert res.unchanged_count == 1
    assert "0 substantive change(s)" in res.summary


def test_modified_amount_and_date():
    pages_a = [
        Page(
            number=1,
            text="The Tenant shall pay a monthly rent of Rs. 25,000.\n\nNotice period shall be thirty (30) days in writing.",
        )
    ]
    pages_b = [
        Page(
            number=1,
            text="The Tenant shall pay a monthly rent of Rs. 32,000.\n\nNotice period shall be sixty (60) days in writing.",
        )
    ]

    res = compare_documents("doc1", "v1.txt", pages_a, "doc2", "v2.txt", pages_b)
    assert res.modified_count == 2
    assert res.total_changes == 2
    # Verify entity change notes
    notes = " ".join(c.significance_note or "" for c in res.changes)
    assert "Rs. 25,000" in notes and "Rs. 32,000" in notes
    assert "30" in notes and "60" in notes


def test_added_and_removed_clauses():
    pages_a = [
        Page(number=1, text="Clause 1: Term of Lease.\n\nClause 2: Pet Policy: No pets are allowed on premises.")
    ]
    pages_b = [
        Page(
            number=1,
            text="Clause 1: Term of Lease.\n\nClause 3: Subletting: Subletting is strictly prohibited without consent.",
        )
    ]

    res = compare_documents("doc1", "v1.txt", pages_a, "doc2", "v2.txt", pages_b)
    assert res.removed_count >= 1
    assert res.added_count >= 1
    types = [c.change_type for c in res.changes]
    assert "removed" in types
    assert "added" in types


def test_formatting_only_changes_suppression():
    pages_a = [Page(number=1, text="The Tenant agrees to keep the premises in good and clean condition.")]
    pages_b = [Page(number=1, text="The  Tenant   agrees to keep the premises in good and clean condition! ")]

    res_no_fmt = compare_documents("doc1", "v1.txt", pages_a, "doc2", "v2.txt", pages_b, include_formatting=False)
    assert res_no_fmt.total_changes == 0
    assert res_no_fmt.formatting_only_count == 1

    res_with_fmt = compare_documents("doc1", "v1.txt", pages_a, "doc2", "v2.txt", pages_b, include_formatting=True)
    assert len(res_with_fmt.changes) == 1
    assert res_with_fmt.changes[0].is_formatting_only


def test_reordered_clauses():
    pages_a = [
        Page(number=1, text="Clause A: Maintenance responsibilities.\n\nClause B: Default terms.\n\nClause C: Dispute resolution.\n\nClause D: Termination notice.")
    ]
    pages_b = [
        Page(number=1, text="Clause D: Termination notice.\n\nClause B: Default terms.\n\nClause C: Dispute resolution.\n\nClause A: Maintenance responsibilities.")
    ]

    res = compare_documents("doc1", "v1.txt", pages_a, "doc2", "v2.txt", pages_b)
    reordered = [c for c in res.changes if c.is_reordered]
    assert len(reordered) >= 1
    for r in reordered:
        assert r.page_before is not None
        assert r.page_after is not None


def test_api_compare_endpoint(tmp_path):
    store = DocumentStore()
    app = create_app(store)

    text_a = (
        b"This is a standard residential tenancy agreement between the landlord and tenant.\n\n"
        b"Monthly rent is Rs. 20,000 payable on 1st of every month in advance.\n\n"
        b"Security deposit is Rs. 40,000 refundable upon expiration.\n\n"
        b"Notice period required for termination is thirty (30) days in writing."
    )
    text_b = (
        b"This is a standard residential tenancy agreement between the landlord and tenant.\n\n"
        b"Monthly rent is Rs. 25,000 payable on 1st of every month in advance.\n\n"
        b"Security deposit is Rs. 50,000 refundable upon expiration.\n\n"
        b"Notice period required for termination is sixty (60) days in writing."
    )

    doc_a = store.upload("lease_v1.txt", text_a)
    doc_b = store.upload("lease_v2.txt", text_b)

    with TestClient(app) as client:
        resp = client.post("/documents/compare", json={"doc_a": doc_a.id, "doc_b": doc_b.id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["doc_a_id"] == doc_a.id
        assert data["doc_b_id"] == doc_b.id
        assert data["modified_count"] >= 2
        assert "Rs. 20,000" in str(data) and "Rs. 25,000" in str(data)

    store.close()
