"""Local OCR engine and scanned document support.

Executes 100% locally with zero external network or cloud API calls.
Integrates with PyMuPDF OCR / Tesseract or a registered local OCR engine.
"""

import os
import shutil
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pymupdf

# Type for custom/test local OCR engine callable: takes (pixmap_bytes, page_number) -> text
OcrHandler = Callable[[bytes, int], str]
_CUSTOM_OCR_HANDLER: OcrHandler | None = None


def set_custom_ocr_handler(handler: OcrHandler | None) -> None:
    """Set or clear a custom local OCR handler (primarily used for deterministic offline tests)."""
    global _CUSTOM_OCR_HANDLER
    _CUSTOM_OCR_HANDLER = handler


def is_tesseract_installed() -> bool:
    """Check if local Tesseract executable or tessdata environment is present."""
    return bool(shutil.which("tesseract") or os.environ.get("TESSDATA_PREFIX"))


def is_local_ocr_available() -> bool:
    """Check if any local OCR capability is operational."""
    if _CUSTOM_OCR_HANDLER is not None:
        return True
    return is_tesseract_installed()


def ocr_page_image(page: "pymupdf.Page", zoom: float = 2.0) -> str:
    """Perform local OCR on a single PyMuPDF page.

    Renders the page to a high-resolution pixmap image locally and processes it.
    Returns the extracted text, or an empty string if nothing could be recognized.
    Raises RuntimeError if local OCR engine is unavailable or encounters a fatal error.
    """
    import pymupdf

    # 1. Check custom handler (e.g. test harness / pluggable engine)
    if _CUSTOM_OCR_HANDLER is not None:
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
        return _CUSTOM_OCR_HANDLER(pix.tobytes("png"), page.number + 1)

    # 2. Check PyMuPDF built-in OCR (backed by local Tesseract/tessdata)
    try:
        textpage = page.get_textpage_ocr(flags=0, language="eng", full=True)
        return textpage.extractText()
    except Exception as exc:
        raise RuntimeError(
            f"Local OCR failed for page {page.number + 1}. Ensure Tesseract is installed locally: {exc}"
        ) from exc
