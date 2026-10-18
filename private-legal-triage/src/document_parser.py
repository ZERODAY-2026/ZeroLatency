import re
from pathlib import Path

import pymupdf

from .config import Settings
from .config import settings as default_settings
from .errors import (
    EncryptedDocument,
    NoExtractableText,
    UnreadableDocument,
    UnsupportedFormat,
)
from .ocr import is_local_ocr_available, ocr_page_image
from .schemas import Page

TEXT_PAGE_CHARS = 3000


def extract_pages(path: str | Path, cfg: Settings = default_settings) -> list[Page]:
    target = Path(path)
    if not target.is_file():
        raise UnreadableDocument("The file could not be found or is not a regular file.")
    if target.stat().st_size > cfg.max_file_bytes:
        raise UnreadableDocument("The file is larger than the supported size limit.")
    suffix = target.suffix.lower()
    if suffix == ".pdf":
        pages = _read_pdf(target, cfg)
    elif suffix == ".txt":
        pages = _read_text(target)
    else:
        raise UnsupportedFormat("Only PDF and plain text (.txt) files are supported.")
    total = sum(len(page.text.strip()) for page in pages)
    if total < cfg.min_total_chars:
        ocr_applied = any(p.is_ocr for p in pages)
        if ocr_applied:
            raise NoExtractableText(
                "Little or no text could be extracted even after applying local OCR. "
                "The document pages may be blank, low-resolution, or unreadable."
            )
        if is_local_ocr_available():
            raise NoExtractableText(
                "Little or no text could be extracted. The document may be blank or corrupted."
            )
        raise NoExtractableText(
            "Little or no text could be extracted. The document appears to be scanned or image-based, "
            "but a local OCR engine (Tesseract) is not installed on this system."
        )
    return pages


def low_text_pages(pages: list[Page], cfg: Settings = default_settings) -> list[int]:
    return [page.number for page in pages if len(page.text.strip()) < cfg.min_chars_per_page]


def _read_pdf(target: Path, cfg: Settings) -> list[Page]:
    # Open from memory stream rather than file path so PyMuPDF does not hold an
    # OS-level file handle on disk, which on Windows prevents immediate unlinking.
    doc = None
    try:
        try:
            doc = pymupdf.open(stream=target.read_bytes(), filetype="pdf")
        except (RuntimeError, ValueError):
            raise UnreadableDocument("The PDF could not be opened. It may be corrupted.") from None
        if doc.needs_pass:
            raise EncryptedDocument("The PDF is password protected and cannot be read.")
        if doc.page_count > cfg.max_pdf_pages:
            raise UnreadableDocument(
                f"The PDF has more than {cfg.max_pdf_pages} pages, which is the supported limit."
            )
        try:
            pages: list[Page] = []
            for i, page in enumerate(doc):
                raw_text = page.get_text("text")
                is_ocr = False
                # If page text is sparse/empty and OCR is enabled and available, attempt local OCR
                if len(raw_text.strip()) < cfg.min_chars_per_page and cfg.ocr_enabled and is_local_ocr_available():
                    try:
                        ocr_text = ocr_page_image(page)
                        if len(ocr_text.strip()) > len(raw_text.strip()):
                            raw_text = ocr_text
                            is_ocr = True
                    except Exception:
                        pass
                pages.append(Page(number=i + 1, text=raw_text, is_ocr=is_ocr))
            return pages
        except (RuntimeError, ValueError):
            raise UnreadableDocument("Text could not be extracted from this PDF.") from None
    finally:
        if doc is not None:
            doc.close()



def _read_text(target: Path) -> list[Page]:
    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise UnreadableDocument("The text file is not valid UTF-8.") from None
    blocks = content.split("\f")
    if len(blocks) == 1:
        blocks = _paginate(content)
    return [Page(number=i + 1, text=block) for i, block in enumerate(blocks)]


def _paginate(content: str) -> list[str]:
    pages: list[str] = []
    current = ""
    for paragraph in re.split(r"\n\s*\n", content):
        if current and len(current) + len(paragraph) > TEXT_PAGE_CHARS:
            pages.append(current)
            current = ""
        current = f"{current}\n\n{paragraph}" if current else paragraph
    if current:
        pages.append(current)
    return pages or [content]
