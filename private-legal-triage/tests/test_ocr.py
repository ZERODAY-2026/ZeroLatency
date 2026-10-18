"""Tests for local OCR capabilities on scanned and image-based PDFs."""

import pymupdf
import pytest

from src.document_parser import extract_pages
from src.errors import NoExtractableText
from src.ocr import set_custom_ocr_handler
from src.privacy import network_guard


def create_text_pdf(tmp_path, text: str) -> str:
    pdf_path = tmp_path / "text_doc.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_textbox(pymupdf.Rect(50, 50, 550, 750), text)
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)


def create_blank_pdf(tmp_path, num_pages: int = 1) -> str:
    pdf_path = tmp_path / "blank_doc.pdf"
    doc = pymupdf.open()
    for _ in range(num_pages):
        doc.new_page()
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)


def test_text_pdf_does_not_invoke_ocr(tmp_path):
    """Text-based PDFs should extract normally without triggering OCR."""
    called = []

    def mock_ocr(pix_bytes: bytes, page_num: int) -> str:
        called.append(page_num)
        return "OCR SHOULD NOT BE CALLED"

    set_custom_ocr_handler(mock_ocr)
    try:
        content = "This is a legitimate standard rental agreement with sufficient extractable text. " * 10
        pdf_path = create_text_pdf(tmp_path, content)
        pages = extract_pages(pdf_path)
        assert len(pages) == 1
        assert not pages[0].is_ocr
        assert not called, "OCR handler was invoked unexpectedly on a text PDF"
    finally:
        set_custom_ocr_handler(None)


def test_scanned_pdf_uses_local_ocr(tmp_path):
    """Scanned/image-only PDF triggers local OCR when available."""
    pdf_path = create_blank_pdf(tmp_path, num_pages=1)
    ocr_text = "This is recognized OCR text from the scanned contract page. " * 8

    def mock_ocr(pix_bytes: bytes, page_num: int) -> str:
        assert len(pix_bytes) > 0
        return ocr_text

    set_custom_ocr_handler(mock_ocr)
    try:
        pages = extract_pages(pdf_path)
        assert len(pages) == 1
        assert pages[0].is_ocr
        assert pages[0].number == 1
        assert "recognized OCR text" in pages[0].text
    finally:
        set_custom_ocr_handler(None)


def test_mixed_pdf_extracts_both_text_and_ocr_pages(tmp_path):
    """Mixed PDF preserves page numbering and associates OCR text with correct page."""
    pdf_path = tmp_path / "mixed.pdf"
    doc = pymupdf.open()
    # Page 1: Native text
    p1 = doc.new_page()
    p1.insert_textbox(pymupdf.Rect(50, 50, 550, 750), "Page 1 standard agreement text with clauses and dates. " * 10)
    # Page 2: Blank/image page needing OCR
    doc.new_page()
    doc.save(str(pdf_path))
    doc.close()

    def mock_ocr(pix_bytes: bytes, page_num: int) -> str:
        if page_num == 2:
            return "Page 2 text recovered via local optical character recognition. " * 8
        return ""

    set_custom_ocr_handler(mock_ocr)
    try:
        pages = extract_pages(str(pdf_path))
        assert len(pages) == 2
        assert pages[0].number == 1
        assert not pages[0].is_ocr
        assert pages[1].number == 2
        assert pages[1].is_ocr
        assert "recovered via local optical" in pages[1].text
    finally:
        set_custom_ocr_handler(None)


def test_scanned_pdf_without_ocr_raises_informative_error(tmp_path):
    """If no local OCR engine is configured/installed, raise informative NoExtractableText."""
    pdf_path = create_blank_pdf(tmp_path, num_pages=1)
    set_custom_ocr_handler(None)
    with pytest.raises(NoExtractableText) as exc:
        extract_pages(pdf_path)
    assert "Little or no text could be extracted" in str(exc.value)


def test_ocr_operates_under_strict_network_guard(tmp_path):
    """Verify that local OCR makes zero outbound network requests."""
    pdf_path = create_blank_pdf(tmp_path, num_pages=1)

    def mock_ocr(pix_bytes: bytes, page_num: int) -> str:
        return "Local OCR safe text under network surveillance. " * 10

    set_custom_ocr_handler(mock_ocr)
    observed = []
    try:
        with network_guard(observed):
            pages = extract_pages(pdf_path)
            assert len(pages) == 1
            assert pages[0].is_ocr
        assert observed == [], "OCR triggered unexpected network activity"
    finally:
        set_custom_ocr_handler(None)
