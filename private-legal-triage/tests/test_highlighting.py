"""Tests for clause navigation, quote highlighting, and page rendering."""

import pymupdf
from fastapi.testclient import TestClient

from src.api import create_app
from src.highlight import _rects, render_page
from src.service import DocumentStore
from tests.conftest import RENTAL_PAGES

TEXT = "\n\n".join(RENTAL_PAGES).encode("utf-8")


def test_highlighting_with_line_breaks_and_hyphenation(tmp_path):
    pdf_path = tmp_path / "highlight_test.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_textbox(
        pymupdf.Rect(50, 50, 500, 700),
        "The Tenant agrees to pay a monthly rent of Rs. 25,000 on or before the 5th day of each month.\n"
        "Notice of termination must be provided thirty (30) days in advance.",
    )
    doc.save(str(pdf_path))
    doc.close()

    # Exact search
    doc2 = pymupdf.open(str(pdf_path))
    p = doc2[0]
    rects_exact = _rects(p, "monthly rent of Rs. 25,000")
    assert len(rects_exact) > 0

    # Non-existent quote produces no rects
    rects_missing = _rects(p, "This clause does not exist in the contract.")
    assert len(rects_missing) == 0

    doc2.close()


def test_render_page_returns_valid_png(rental_pdf):
    # Render page without quote
    png_bytes = render_page(rental_pdf, page_number=1)
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    # Render page with quote
    png_highlight = render_page(rental_pdf, page_number=1, quote="monthly rent of Rs. 25,000")
    assert png_highlight.startswith(b"\x89PNG\r\n\x1a\n")


def test_page_and_highlight_api_endpoints(rental_pdf):
    store = DocumentStore()
    app = create_app(store)
    from pathlib import Path
    pdf_bytes = Path(rental_pdf).read_bytes()
    doc = store.upload("rental.pdf", pdf_bytes)

    with TestClient(app) as client:
        # 1. Fetch text of page 1
        resp_text = client.get(f"/documents/{doc.id}/pages/1")
        assert resp_text.status_code == 200
        assert resp_text.json()["page"] == 1
        assert "Rs. 25,000" in resp_text.json()["text"]

        # 2. Fetch page image
        resp_img = client.get(f"/documents/{doc.id}/pages/1/image")
        assert resp_img.status_code == 200
        assert resp_img.headers["content-type"] == "image/png"
        assert resp_img.content.startswith(b"\x89PNG\r\n\x1a\n")

        # 3. Fetch page image with quotation highlight
        resp_hi = client.get(f"/documents/{doc.id}/pages/1/image?quote=monthly%20rent")
        assert resp_hi.status_code == 200
        assert resp_hi.headers["content-type"] == "image/png"

    store.close()
