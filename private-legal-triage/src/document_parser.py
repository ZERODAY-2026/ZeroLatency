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
        raise NoExtractableText(
            "Little or no text could be extracted. If this is a scanned document, note that "
            "local OCR is not supported yet."
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
            return [Page(number=i + 1, text=page.get_text("text")) for i, page in enumerate(doc)]
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
