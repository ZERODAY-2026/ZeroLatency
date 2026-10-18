from src.citation_validator import SourceIndex, normalize, validate_all, validate_candidate
from src.schemas import Candidate, Page

PAGES = [
    Page(
        number=1,
        text="The Tenant shall pay monthly rent of Rs. 25,000 on\nor before the 5th day of each month.",
    ),
    Page(number=2, text="The Tenant may terminate this agreement by giving 60 days\u2019 written notice."),
]


def candidate(quote, page=1, **kw):
    base = dict(
        category="obligation",
        title="Rent",
        explanation="Rent is Rs. 25,000 monthly.",
        evidence_quote=quote,
        statement_type="explicit",
        page=page,
        chunk_id="p1_c1",
    )
    base.update(kw)
    return Candidate(**base)


def test_normalization_is_documented_behaviour():
    assert normalize("A\u00a0 \u201cquote\u201d\u2014x") == 'a "quote"-x'


def test_exact_quote_verified_across_line_break():
    f = validate_candidate(
        candidate("monthly rent of Rs. 25,000 on or before the 5th day"), SourceIndex(PAGES)
    )
    assert f.verification_status == "verified"
    assert f.confidence == "high"
    assert not f.needs_human_review


def test_curly_apostrophe_matches():
    f = validate_candidate(
        candidate("giving 60 days' written notice", page=2, explanation="Needs 60 days notice."),
        SourceIndex(PAGES),
    )
    assert f.verification_status == "verified"


def test_fabricated_quote_is_unverified():
    f = validate_candidate(candidate("The Tenant owes a penalty of Rs. 90,000 per day."), SourceIndex(PAGES))
    assert f.verification_status == "unverified"
    assert f.confidence == "low"
    assert f.needs_human_review


def test_wrong_page_is_corrected():
    f = validate_candidate(
        candidate("giving 60 days\u2019 written notice", page=1, explanation="60 days notice."),
        SourceIndex(PAGES),
    )
    assert f.verification_status == "verified"
    assert f.page == 2
    assert "corrected" in f.verification_note


def test_nonexistent_page_unverified():
    f = validate_candidate(candidate("monthly rent of Rs. 25,000", page=9), SourceIndex(PAGES))
    assert f.verification_status == "unverified"
    assert "does not exist" in f.verification_note


def test_short_quote_rejected():
    f = validate_candidate(candidate("rent"), SourceIndex(PAGES))
    assert f.verification_status == "unverified"


def test_invented_figure_lowers_confidence():
    f = validate_candidate(
        candidate("monthly rent of Rs. 25,000", explanation="Rent is Rs. 40,000 monthly."), SourceIndex(PAGES)
    )
    assert f.verification_status == "verified"
    assert "40000" in f.ungrounded_figures
    assert f.confidence == "low"
    assert f.needs_human_review


def test_number_words_are_grounded():
    pages = [Page(number=1, text="The notice period is thirty days from the date of the written notice.")]
    f = validate_candidate(
        candidate("The notice period is thirty days", explanation="You must give 30 days notice."),
        SourceIndex(pages),
    )
    assert f.ungrounded_figures == []


def test_interpretation_and_jurisdiction_need_review():
    f = validate_candidate(
        candidate("monthly rent of Rs. 25,000", statement_type="interpretation"), SourceIndex(PAGES)
    )
    assert f.confidence == "medium" and f.needs_human_review
    g = validate_candidate(
        candidate("monthly rent of Rs. 25,000", jurisdiction_dependent=True), SourceIndex(PAGES)
    )
    assert g.needs_human_review


def test_verified_sorted_first():
    items = [candidate("not in the document at all, invented text"), candidate("monthly rent of Rs. 25,000")]
    out = validate_all(items, SourceIndex(PAGES))
    assert [f.verification_status for f in out] == ["verified", "unverified"]


def test_fuzzy_quote_with_minor_word_substitution_is_verified():
    # Document has "The Tenant shall pay monthly rent of Rs. 25,000 on or before the 5th day"
    # Quote has "will" instead of "shall" (high confidence >85% match)
    f = validate_candidate(
        candidate("The Tenant will pay monthly rent of Rs. 25,000 on or before the 5th day"),
        SourceIndex(PAGES),
    )
    assert f.verification_status == "verified"
    assert f.page == 1

