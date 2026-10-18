import re
import unicodedata

from .config import Settings
from .config import settings as default_settings
from .facts import numeric_tokens
from .schemas import Candidate, Finding, Page

TRANSLATION = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u00a0": " ",
    }
)
QUOTE_EDGES = " \t\r\n\"'\u201c\u201d\u2018\u2019`"
REVIEW_CATEGORIES = {"risk", "ambiguity"}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(TRANSLATION)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().casefold()


class SourceIndex:
    def __init__(self, pages: list[Page], cfg: Settings = default_settings):
        self.min_quote_chars = cfg.min_quote_chars
        self.raw = {page.number: page.text for page in pages}
        self.normalized = {number: normalize(text) for number, text in self.raw.items()}

    def has_page(self, number: int) -> bool:
        return number in self.raw

    def locate(self, quote: str, preferred: int | None = None) -> int | None:
        needle = normalize(quote.strip(QUOTE_EDGES))
        if len(needle) < self.min_quote_chars:
            return None
        if preferred in self.normalized and needle in self.normalized[preferred]:
            return preferred
        for number in sorted(self.normalized):
            if needle in self.normalized[number]:
                return number
        return None

    def window_text(self, page: int | None) -> str:
        if page is None:
            return " ".join(self.raw.values())
        return " ".join(self.raw.get(n, "") for n in (page - 1, page, page + 1))


def ungrounded_figures(explanation: str, source: str) -> list[str]:
    allowed = numeric_tokens(source)
    return sorted(numeric_tokens(explanation) - allowed, key=lambda token: (len(token), token))


def validate_candidate(candidate: Candidate, index: SourceIndex) -> Finding:
    located = index.locate(candidate.evidence_quote, candidate.page)
    page = candidate.page
    if not index.has_page(candidate.page):
        status, note = "unverified", "The cited page does not exist in the document."
    elif located is None:
        status, note = "unverified", "The quotation could not be found in the extracted text."
    elif located != candidate.page:
        page = located
        status = "verified"
        note = f"Quotation found on page {located}; page corrected from {candidate.page}."
    else:
        status, note = "verified", "Quotation matches the source text after documented normalization."

    scope = index.window_text(located if status == "verified" else None)
    figures = ungrounded_figures(f"{candidate.title} {candidate.explanation}", scope)
    if figures:
        note += " Figures in the explanation do not appear in the source: " + ", ".join(figures) + "."

    if status == "unverified" or figures:
        confidence = "low"
    elif candidate.statement_type == "explicit":
        confidence = "high"
    else:
        confidence = "medium"

    needs_review = (
        confidence != "high" or candidate.jurisdiction_dependent or candidate.category in REVIEW_CATEGORIES
    )
    data = candidate.model_dump()
    data["page"] = page
    return Finding(
        **data,
        verification_status=status,
        verification_note=note,
        confidence=confidence,
        needs_human_review=needs_review,
        ungrounded_figures=figures,
    )


def validate_all(candidates: list[Candidate], index: SourceIndex) -> list[Finding]:
    findings = [validate_candidate(candidate, index) for candidate in candidates]
    return sorted(findings, key=lambda f: (f.verification_status != "verified", f.page))
