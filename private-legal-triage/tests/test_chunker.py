from src.chunker import chunk_pages
from src.config import Settings
from src.schemas import Page


def test_ids_and_pages_preserved():
    pages = [
        Page(number=1, text="1. TERM\nOne year.\n2. RENT\nPaid monthly."),
        Page(number=3, text="3. LAW\nIndia."),
    ]
    chunks = chunk_pages(pages)
    assert [c.chunk_id for c in chunks] == ["p1_c1", "p3_c1"]
    assert [c.page for c in chunks] == [1, 3]


def test_clauses_split_when_budget_small():
    cfg = Settings(chunk_max_chars=60, chunk_overlap_chars=10)
    text = "1. TERM\nThe term is eleven months long.\n2. RENT\nRent is due on the fifth day.\n3. LAW\nIndian law."
    chunks = chunk_pages([Page(number=1, text=text)], cfg)
    assert len(chunks) >= 2
    assert all(c.page == 1 for c in chunks)
    assert chunks[0].text.startswith("1. TERM")


def test_long_segment_is_hard_split_with_overlap():
    cfg = Settings(chunk_max_chars=200, chunk_overlap_chars=40)
    text = "Sentence number one is here. " * 40
    chunks = chunk_pages([Page(number=2, text=text)], cfg)
    assert len(chunks) > 1
    assert all(len(c.text) <= 200 for c in chunks)
    assert all(c.chunk_id.startswith("p2_c") for c in chunks)


def test_empty_pages_skipped():
    assert chunk_pages([Page(number=1, text="   \n ")]) == []
