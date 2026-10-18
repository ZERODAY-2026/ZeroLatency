import pymupdf
import pytest

from samples.make_samples import write_pdf
from src.document_parser import extract_pages, low_text_pages
from src.errors import EncryptedDocument, NoExtractableText, UnreadableDocument, UnsupportedFormat


def test_pdf_pages_are_numbered(rental_pdf):
    pages = extract_pages(rental_pdf)
    assert [p.number for p in pages] == [1, 2]
    assert "SECURITY DEPOSIT" in pages[0].text
    assert "TERMINATION" in pages[1].text


def test_text_file_is_supported(rental_txt):
    pages = extract_pages(rental_txt)
    assert pages and "RESIDENTIAL LEASE" in pages[0].text


def test_unsupported_extension(tmp_path):
    path = tmp_path / "notes.docx"
    path.write_bytes(b"x")
    with pytest.raises(UnsupportedFormat):
        extract_pages(path)


def test_missing_file(tmp_path):
    with pytest.raises(UnreadableDocument):
        extract_pages(tmp_path / "absent.pdf")


def test_corrupt_pdf(tmp_path):
    path = tmp_path / "bad.pdf"
    path.write_bytes(b"this is not a pdf at all")
    with pytest.raises(UnreadableDocument):
        extract_pages(path)


def test_encrypted_pdf(tmp_path):
    plain = write_pdf(tmp_path / "plain.pdf", ["Some text " * 40])
    locked = tmp_path / "locked.pdf"
    with pymupdf.open(plain) as doc:
        doc.save(str(locked), encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="u", owner_pw="o")
    with pytest.raises(EncryptedDocument):
        extract_pages(locked)


def test_blank_pdf_has_no_text(tmp_path):
    doc = pymupdf.open()
    doc.new_page()
    path = tmp_path / "blank.pdf"
    doc.save(str(path))
    with pytest.raises(NoExtractableText):
        extract_pages(path)


def test_low_text_pages_detected(tmp_path):
    path = write_pdf(tmp_path / "mixed.pdf", ["Real clause text. " * 30, "x"])
    assert low_text_pages(extract_pages(path)) == [2]


def test_non_utf8_text(tmp_path):
    path = tmp_path / "latin.txt"
    path.write_bytes(b"\xff\xfe\x00bad")
    with pytest.raises(UnreadableDocument):
        extract_pages(path)
