from src.document_parser import extract_pages
from src.facts import extract_key_facts, numeric_tokens


def test_key_facts_extracted_with_pages(rental_pdf):
    facts = extract_key_facts(extract_pages(rental_pdf))
    by_label = {}
    for fact in facts:
        by_label.setdefault(fact.label, []).append(fact)
    assert any("25,000" in f.value for f in by_label["amount"])
    assert any(f.value.startswith("2%") for f in by_label["percentage"])
    assert any("30 days" in f.value for f in by_label["duration"])
    assert any("1 November 2026" in f.value for f in by_label["date"])
    assert any("India" in f.value for f in by_label.get("jurisdiction", []))
    assert all(f.page in (1, 2) for f in facts)


def test_numeric_tokens_handle_words_and_commas():
    assert {"30", "25000", "25"} <= numeric_tokens("thirty days, Rs. 25,000, twenty-five percent")


def test_checklist_reports_found_and_missing(rental_pdf):
    from src.checklist import scan_checklist
    items = {i.topic: i for i in scan_checklist(extract_pages(rental_pdf))}
    assert items["termination"].found and items["termination"].pages == [2]
    assert items["governing law"].found
    assert not items["force majeure"].found
    assert not items["indemnity"].found


def test_structured_fact_subtypes_and_conflicts():
    from src.schemas import Page
    pages = [
        Page(number=1, text="The Tenant shall pay a monthly rent of Rs. 25,000 and a refundable deposit of Rs. 75,000."),
        Page(number=2, text="In case of renewal, the monthly rent shall be Rs. 30,000. Notice period is thirty (30) days."),
    ]
    facts = extract_key_facts(pages)

    # Subtypes identified correctly
    subtypes = {f.fact_subtype for f in facts}
    assert "monthly_rent" in subtypes
    assert "security_deposit" in subtypes
    assert "notice_period" in subtypes

    # Normalized values populated
    rent_facts = [f for f in facts if f.fact_subtype == "monthly_rent"]
    assert len(rent_facts) == 2
    assert 25000.0 in [f.normalized_value for f in rent_facts]
    assert 30000.0 in [f.normalized_value for f in rent_facts]

    # Conflicting rent amounts flagged
    assert all(f.conflicting for f in rent_facts)

    # Non-conflicting deposit not flagged
    deposit_fact = next(f for f in facts if f.fact_subtype == "security_deposit")
    assert not deposit_fact.conflicting
    assert deposit_fact.normalized_value == 75000.0
