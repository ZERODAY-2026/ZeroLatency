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


def _normalize_fact_value(label: str, value: str) -> str | float | int | None:
    try:
        if label == "amount":
            val_num = re.sub(r"^(?:₹|\$|(?:Rs\.?|INR|USD))\s*", "", value, flags=re.I).strip()
            clean = re.sub(r"[^\d.]", "", val_num.replace(",", ""))
            if clean:
                factor = 1.0
                if re.search(r"lakh", value, re.I):
                    factor = 100_000.0
                elif re.search(r"crore", value, re.I):
                    factor = 10_000_000.0
                elif re.search(r"thousand", value, re.I):
                    factor = 1_000.0
                elif re.search(r"million", value, re.I):
                    factor = 1_000_000.0
                return round(float(clean) * factor, 2)
        elif label == "percentage":
            clean = re.sub(r"[^\d.]", "", value)
            if clean:
                return float(clean)
        elif label == "duration":
            digits = re.search(r"\d+", value)
            if digits:
                return int(digits.group())
            for word, num in {**UNITS, **TENS}.items():
                if re.search(rf"\b{word}\b", value, re.I):
                    return num
    except Exception:
        pass
    return value.strip()


def _infer_fact_subtype(label: str, snippet: str, pre_text: str = "") -> str:
    p = pre_text.lower()
    s = snippet.lower()
    if label == "amount":
        if "rent" in p or "monthly" in p:
            return "monthly_rent"
        if "deposit" in p:
            return "security_deposit"
        if "penalty" in p or "fine" in p or "late" in p:
            return "penalty_charge"
        if "rent" in s or "monthly" in s:
            return "monthly_rent"
        if "deposit" in s:
            return "security_deposit"
        return "monetary_amount"
    elif label == "duration":
        if "notice" in p or "terminat" in p:
            return "notice_period"
        if "lease" in p or "term" in p:
            return "lease_term"
        if "notice" in s or "terminat" in s:
            return "notice_period"
        if "lease" in s or "term" in s:
            return "lease_term"
        if "grace" in s:
            return "grace_period"
        return "duration_period"
    elif label == "party":
        if "landlord" in s or "lessor" in s:
            return "landlord"
        if "tenant" in s or "lessee" in s:
            return "tenant"
        return "contracting_party"
    elif label == "date":
        if "commence" in s or "start" in s or "effective" in s:
            return "commencement_date"
        if "expir" in s or "end" in s or "terminat" in s:
            return "expiration_date"
        if "sign" in s or "execut" in s:
            return "execution_date"
        return "calendar_date"
    return label


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
            pre_text = flat[max(0, start - 40) : start].strip()
            subtype = _infer_fact_subtype(label, snippet, pre_text)
            normalized = _normalize_fact_value(label, value)
            facts.append(
                KeyFact(
                    label=label,
                    value=value,
                    page=page.number,
                    snippet=snippet,
                    normalized_value=normalized,
                    fact_subtype=subtype,
                    conflicting=False,
                )
            )

    # Flag conflicting facts with different normalized values for specific key subtypes
    subtype_vals: dict[str, set[str]] = {}
    for f in facts:
        if f.fact_subtype in ("monthly_rent", "security_deposit", "notice_period") and f.normalized_value is not None:
            norm_str = str(f.normalized_value)
            subtype_vals.setdefault(f.fact_subtype, set()).add(norm_str)

    for f in facts:
        if f.fact_subtype in subtype_vals and len(subtype_vals[f.fact_subtype]) > 1:
            f.conflicting = True

    return facts
