from src.checklist import scan_checklist
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
    items = {i.topic: i for i in scan_checklist(extract_pages(rental_pdf))}
    assert items["termination"].found and items["termination"].pages == [2]
    assert items["governing law"].found
    assert not items["force majeure"].found
    assert not items["indemnity"].found
