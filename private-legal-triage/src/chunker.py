import re

from .config import Settings
from .config import settings as default_settings
from .schemas import Chunk, Page

CLAUSE_START = re.compile(
    r"^(?=\s*(?:(?i:article|section|clause|schedule)\b|\d+(?:\.\d+)*[.)]\s|[A-Z][A-Z0-9 ,&\-]{5,}$))",
    re.MULTILINE,
)


def chunk_pages(pages: list[Page], cfg: Settings = default_settings) -> list[Chunk]:
    chunks: list[Chunk] = []
    for page in pages:
        text = page.text.strip()
        if not text:
            continue
        for index, piece in enumerate(_pack(_segments(text), cfg), start=1):
            chunks.append(Chunk(chunk_id=f"p{page.number}_c{index}", page=page.number, text=piece))
    return chunks


def _segments(text: str) -> list[str]:
    return [part.strip() for part in CLAUSE_START.split(text) if part.strip()]


def _pack(segments: list[str], cfg: Settings) -> list[str]:
    packed: list[str] = []
    current = ""
    for segment in segments:
        if len(segment) > cfg.chunk_max_chars:
            if current:
                packed.append(current)
                current = ""
            packed.extend(_hard_split(segment, cfg.chunk_max_chars, cfg.chunk_overlap_chars))
            continue
        if current and len(current) + len(segment) + 1 > cfg.chunk_max_chars:
            packed.append(current)
            current = ""
        current = f"{current}\n{segment}" if current else segment
    if current:
        packed.append(current)
    return packed


def _hard_split(text: str, max_chars: int, overlap: int) -> list[str]:
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            cut = max(text.rfind(". ", start, end), text.rfind("\n", start, end))
            if cut > start + max_chars // 2:
                end = cut + 1
        parts.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [part for part in parts if part]
