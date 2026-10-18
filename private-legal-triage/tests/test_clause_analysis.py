"""Tests for conflicting and unusual clause detection."""

from src.clause_analysis import detect_conflicts, detect_unusual_clauses
from src.schemas import Page


def test_contradictory_notice_periods():
    pages = [
        Page(number=1, text="The Tenant may terminate this lease by providing thirty (30) days notice in writing."),
        Page(number=2, text="Standard operations and rules."),
        Page(number=3, text="For termination by either party, sixty (60) days notice is required prior to vacating."),
    ]
    conflicts = detect_conflicts(pages)
    assert len(conflicts) >= 1
    types = [c.conflict_type for c in conflicts]
    assert "contradictory_notice_period" in types
    c = next(c for c in conflicts if c.conflict_type == "contradictory_notice_period")
    assert c.page_a == 1
    assert c.page_b == 3
    assert "thirty (30) days" in c.description and "sixty (60) days" in c.description


def test_contradictory_rent_amounts():
    pages = [
        Page(number=1, text="The Tenant agrees to pay a monthly rent of Rs. 25,000 on the first day of each month."),
        Page(number=4, text="The rental payment shall be Rs. 35,000 per month payable in advance."),
    ]
    conflicts = detect_conflicts(pages)
    assert len(conflicts) >= 1
    c = next(c for c in conflicts if c.conflict_type == "contradictory_rent_amount")
    assert c.page_a == 1
    assert c.page_b == 4
    assert "Rs. 25,000" in c.description and "Rs. 35,000" in c.description


def test_unusual_clause_detection():
    pages = [
        Page(
            number=2,
            text="The Landlord reserves the right to modify the terms of this agreement at any time without notice.",
        ),
        Page(
            number=3,
            text="The Tenant agrees to waive all claims and release Landlord from gross negligence.",
        ),
    ]
    unusual = detect_unusual_clauses(pages)
    assert len(unusual) >= 2
    types = [u.clause_type for u in unusual]
    assert "unilateral_modification" in types
    assert "waiver_of_liability_negligence" in types
    for item in unusual:
        assert item.needs_human_review is True
        assert "not determine whether the clause is legally valid" in item.disclaimer
