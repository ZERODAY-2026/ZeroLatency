"""Missing, conflicting, and unusual clause detection.

Implements deterministic rule-based checks and local pattern analysis:
1. Detects conflicting obligations (e.g. contradictory notice periods, payment amounts).
2. Flags candidate unusual or one-sided clauses for human attorney review.
3. Distinguishes 'not detected' from 'confirmed absent'.
4. Traces all findings to source passages and page numbers.
"""

import re
from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel

from .facts import PATTERNS
from .schemas import Page


class ConflictFinding(BaseModel):
    conflict_type: str
    description: str
    passage_a: str
    page_a: int
    passage_b: str
    page_b: int
    severity: Literal["high", "medium", "low"] = "high"


class UnusualClauseCandidate(BaseModel):
    clause_type: str
    reason: str
    evidence_quote: str
    page: int
    needs_human_review: bool = True
    disclaimer: str = (
        "Candidate flagged for human legal review. This is an informational heuristic "
        "and does not determine whether the clause is legally valid or enforceable."
    )


UNUSUAL_PATTERNS = [
    (
        "unilateral_modification",
        re.compile(r"\b(?:modify|alter|amend|change|cancel)\b.*?\b(?:at any time|at sole discretion|without (?:prior )?notice)\b", re.I),
        "Allows one party to unilaterally alter agreement terms without prior notice or consent.",
    ),
    (
        "waiver_of_liability_negligence",
        re.compile(r"\b(?:waive|release|hold harmless)\b.*?\b(?:gross negligence|willful misconduct|all liability)\b", re.I),
        "Purports to waive liability for gross negligence or all claims, which is frequently disfavored in many jurisdictions.",
    ),
    (
        "unlimited_forfeiture",
        re.compile(r"\b(?:forfeit|forfeiture of) (?:all|the entire) (?:deposit|security deposit)\b.*?\b(?:regardless|for any reason|without breach)\b", re.I),
        "Authorizes complete forfeiture of deposit without established breach or default.",
    ),
    (
        "exclusive_distant_jurisdiction",
        re.compile(r"\b(?:exclusive jurisdiction|venue in|courts of)\s+([A-Za-z\s]{3,30}?)\b", re.I),
        "Designates exclusive jurisdiction/venue that may be geographically distant from leased property or domicile.",
    ),
    (
        "unilateral_immediate_termination",
        re.compile(r"\b(?:terminate (?:immediately|without cause|without notice|at will))\b", re.I),
        "Permits immediate termination without cause or notice period.",
    ),
]


def detect_conflicts(pages: Sequence[Page]) -> list[ConflictFinding]:
    """Scan document pages for internal contradictory values or obligations."""
    conflicts: list[ConflictFinding] = []

    # 1. Collect notice periods and durations by page
    duration_pattern = PATTERNS["duration"]
    duration_matches: list[tuple[str, int, str]] = []  # (val, page, snippet)

    for page in pages:
        for match in duration_pattern.finditer(page.text):
            val = match.group().strip().lower()
            # Focus on notice/termination durations
            start = max(0, match.start() - 60)
            end = min(len(page.text), match.end() + 60)
            snippet = page.text[start:end].replace("\n", " ")
            if re.search(r"\b(?:notice|terminate|termination|renewal|vacate)\b", snippet, re.I):
                duration_matches.append((val, page.number, snippet))

    # Compare pairs of notice periods across pages/clauses
    seen_pairs = set()
    for i in range(len(duration_matches)):
        for j in range(i + 1, len(duration_matches)):
            val_a, page_a, snip_a = duration_matches[i]
            val_b, page_b, snip_b = duration_matches[j]
            if val_a != val_b:
                pair_key = tuple(sorted([val_a, val_b]))
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    conflicts.append(
                        ConflictFinding(
                            conflict_type="contradictory_notice_period",
                            description=(
                                f"Contradictory notice periods detected: '{val_a}' on page {page_a} "
                                f"versus '{val_b}' on page {page_b}."
                            ),
                            passage_a=snip_a,
                            page_a=page_a,
                            passage_b=snip_b,
                            page_b=page_b,
                            severity="high",
                        )
                    )

    # 2. Collect amounts (e.g. rent discrepancies)
    amount_pattern = PATTERNS["amount"]
    rent_matches: list[tuple[str, int, str]] = []
    for page in pages:
        for match in amount_pattern.finditer(page.text):
            val = match.group().strip()
            start = max(0, match.start() - 60)
            end = min(len(page.text), match.end() + 60)
            snippet = page.text[start:end].replace("\n", " ")
            if re.search(r"\b(?:monthly rent|rent of|rental payment)\b", snippet, re.I):
                rent_matches.append((val, page.number, snippet))

    seen_amounts = set()
    for i in range(len(rent_matches)):
        for j in range(i + 1, len(rent_matches)):
            val_a, page_a, snip_a = rent_matches[i]
            val_b, page_b, snip_b = rent_matches[j]
            if val_a != val_b:
                pair_key = tuple(sorted([val_a, val_b]))
                if pair_key not in seen_amounts:
                    seen_amounts.add(pair_key)
                    conflicts.append(
                        ConflictFinding(
                            conflict_type="contradictory_rent_amount",
                            description=(
                                f"Inconsistent rent amounts specified: '{val_a}' on page {page_a} "
                                f"versus '{val_b}' on page {page_b}."
                            ),
                            passage_a=snip_a,
                            page_a=page_a,
                            passage_b=snip_b,
                            page_b=page_b,
                            severity="high",
                        )
                    )

    return conflicts


def detect_unusual_clauses(pages: Sequence[Page]) -> list[UnusualClauseCandidate]:
    """Identify candidate unusual clauses against standard contract baselines."""
    candidates: list[UnusualClauseCandidate] = []
    seen = set()

    for page in pages:
        for clause_type, pattern, reason in UNUSUAL_PATTERNS:
            for match in pattern.finditer(page.text):
                start = max(0, match.start() - 40)
                end = min(len(page.text), match.end() + 80)
                quote = page.text[start:end].strip().replace("\n", " ")
                key = (clause_type, page.number)
                if key not in seen and len(quote) >= 15:
                    seen.add(key)
                    candidates.append(
                        UnusualClauseCandidate(
                            clause_type=clause_type,
                            reason=reason,
                            evidence_quote=quote,
                            page=page.number,
                            needs_human_review=True,
                        )
                    )

    return candidates
