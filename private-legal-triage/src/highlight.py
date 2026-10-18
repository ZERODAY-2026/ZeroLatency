import re
from pathlib import Path

import pymupdf

from .errors import DocumentError, UnreadableDocument, UnsupportedFormat


def _rects(page: pymupdf.Page, quote: str) -> list[pymupdf.Rect]:
    flat = re.sub(r"\s+", " ", quote).strip()
    if len(flat) < 5:
        return []

    # 1. Direct search
    rects = page.search_for(flat)
    if rects:
        return rects

    # 2. Try de-hyphenated search
    dehyphen = re.sub(r"(\w)-\s+(\w)", r"\1\2", flat)
    if dehyphen != flat:
        rects = page.search_for(dehyphen)
        if rects:
            return rects

    # 3. Sentence or clause fragment search
    found: list[pymupdf.Rect] = []
    for piece in re.split(r"(?<=[.;:,])\s+", flat):
        piece_clean = piece.strip()
        if len(piece_clean) >= 15:
            r = page.search_for(piece_clean)
            if r:
                found.extend(r)
    return found


def render_page(path: str | Path, page_number: int, quote: str | None = None, zoom: float = 2.0) -> bytes:
    target = Path(path)
    if target.suffix.lower() != ".pdf":
        raise UnsupportedFormat("Page rendering is only available for PDF files.")
    try:
        doc = pymupdf.open(target)
    except (RuntimeError, ValueError):
        raise UnreadableDocument("The PDF could not be opened.") from None
    with doc:
        if not 1 <= page_number <= doc.page_count:
            raise DocumentError("That page does not exist in the document.")
        page = doc[page_number - 1]
        if quote:
            for rect in _rects(page, quote):
                page.add_highlight_annot(rect)
        return page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).tobytes("png")
