"""Local OCR engine and scanned document support.

Executes 100% locally with zero external network or cloud API calls.
Integrates with PyMuPDF OCR / Tesseract or a registered local OCR engine.
"""

import os
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pymupdf

# Type for custom/test local OCR engine callable: takes (pixmap_bytes, page_number) -> text
OcrHandler = Callable[[bytes, int], str]
_CUSTOM_OCR_HANDLER: OcrHandler | None = None

COMMON_WINDOWS_TESSERACT_DIRS = [
    Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Tesseract-OCR",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR",
    Path(r"C:\Program Files (x86)\Tesseract-OCR"),
]


def set_custom_ocr_handler(handler: OcrHandler | None) -> None:
    """Set or clear a custom local OCR handler (primarily used for deterministic offline tests)."""
    global _CUSTOM_OCR_HANDLER
    _CUSTOM_OCR_HANDLER = handler


BUNDLED_TESSDATA_DIR = Path(__file__).parent.parent / "tessdata"


def find_tessdata_dir() -> str | None:
    """Locate local tessdata directory on Windows/Linux systems."""
    # 1. Bundled local tessdata directory in the project
    if BUNDLED_TESSDATA_DIR.is_dir() and (BUNDLED_TESSDATA_DIR / "eng.traineddata").is_file():
        return str(BUNDLED_TESSDATA_DIR)

    # 2. Explicit environment variable
    env_tessdata = os.environ.get("TESSDATA_PREFIX")
    if env_tessdata and Path(env_tessdata).is_dir():
        return env_tessdata

    # 2. From tesseract binary in PATH
    which = shutil.which("tesseract")
    if which:
        candidate = Path(which).parent / "tessdata"
        if candidate.is_dir():
            return str(candidate)

    # 3. Common Windows installation paths
    for base_dir in COMMON_WINDOWS_TESSERACT_DIRS:
        tessdata = base_dir / "tessdata"
        if tessdata.is_dir():
            return str(tessdata)

    return None


def is_tesseract_installed() -> bool:
    """Check if local Tesseract executable or tessdata environment is present."""
    if shutil.which("tesseract") or os.environ.get("TESSDATA_PREFIX"):
        return True
    return find_tessdata_dir() is not None


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
    tessdata = find_tessdata_dir()
    try:
        kwargs: dict[str, object] = {"flags": 0, "language": "eng", "full": True}
        if tessdata:
            kwargs["tessdata"] = tessdata
        textpage = page.get_textpage_ocr(**kwargs)
        return textpage.extractText()
    except Exception as exc:
        raise RuntimeError(
            f"Local OCR failed for page {page.number + 1}. Ensure Tesseract is installed locally: {exc}"
        ) from exc
