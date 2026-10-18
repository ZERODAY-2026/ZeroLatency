import re

from .schemas import KeyFact, Page

MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December|"
    "Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec"
)
UNITS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}
TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
WORDS = "|".join(sorted([*UNITS, *TENS, "hundred"], key=len, reverse=True))
COMPOUND = re.compile(
    rf"\b({'|'.join(TENS)})[\s-]({'|'.join(k for k, v in UNITS.items() if v < 10)})\b", re.I
)
WORD_NUMBER = re.compile(rf"\b({WORDS})\b", re.I)
DIGITS = re.compile(r"\d+(?:,\d{2,3})*(?:\.\d+)?")

PATTERNS: dict[str, re.Pattern[str]] = {
    "amount": re.compile(
        r"(?:₹|\$|(?<![A-Za-z])(?:Rs\.?|INR|USD))\s?\d[\d,]*(?:\.\d+)?"
        r"(?:\s?(?:lakhs?|crores?|thousand|million))?",
        re.I,
    ),
    "percentage": re.compile(r"\d+(?:\.\d+)?\s?(?:%|per\s?cent)", re.I),
    "duration": re.compile(
        rf"\b(?:\d+|{WORDS})(?:\s*\(\d+\))?[\s-]*(?:calendar\s+|business\s+|working\s+)?"
        r"(?:days?|weeks?|months?|years?)\b",
        re.I,
    ),
    "date": re.compile(
        rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:{MONTHS})\.?,?\s+\d{{4}}\b"
        rf"|\b(?:{MONTHS})\.?\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b"
        r"|\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b",
        re.I,
    ),
    "jurisdiction": re.compile(
        r"\b(?:governed by(?: the laws of)?|laws of|jurisdiction of(?: the courts of)?|arbitration in)\s+([A-Za-z\s]{3,30}?)(?=[.;,\n]|\band\b)",
        re.I,
    ),
    "party": re.compile(
        r"\bbetween\s+([A-Z][A-Za-z0-9\s.,&]{2,50}?)(?:\s*\([^)]+\))?\s+and\s+([A-Z][A-Za-z0-9\s.,&]{2,50}?)(?:\s*\([^)]+\))?(?=[.;,\n]|\bfor\b)",
        re.I,
    ),
}


def numeric_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for match in COMPOUND.finditer(text):
        tokens.add(str(TENS[match.group(1).lower()] + UNITS[match.group(2).lower()]))
    for match in WORD_NUMBER.finditer(text):
        word = match.group(1).lower()
        tokens.add(str(100 if word == "hundred" else TENS.get(word) or UNITS[word]))
    for match in DIGITS.finditer(text):
        tokens.add(match.group().replace(",", ""))
    return tokens


def extract_key_facts(pages: list[Page]) -> list[KeyFact]:
    facts: list[KeyFact] = []
    seen: set[tuple[str, str, int]] = set()
    for page in pages:
        flat = re.sub(r"\s+", " ", page.text)
        found: list[tuple[int, str, str]] = []
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(flat):
                found.append((match.start(), label, match.group()))
        for start, label, value in sorted(found):
            key = (label, value.lower(), page.number)
            if key in seen:
                continue
            seen.add(key)
            snippet = flat[max(0, start - 60) : start + len(value) + 60].strip()
            facts.append(KeyFact(label=label, value=value, page=page.number, snippet=snippet))
    return facts
