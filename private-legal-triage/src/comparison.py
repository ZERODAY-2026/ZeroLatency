"""Two-version document comparison module.

Performs local-first alignment and diffing between two legal documents:
1. Normalizes and segments clauses/sections with page tracking.
2. Aligns clauses using sequence matching and lexical similarity.
3. Detects added, removed, modified, reordered, and unchanged clauses.
4. Identifies substantive changes (dates, amounts, notice periods, terms)
   versus formatting-only changes (whitespace, punctuation, case).
5. Preserves exact before-and-after source text and source page references.
6. Distinguishes direct textual diffs from interpretations of significance.
"""

import difflib
import re
from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, Field

from .citation_validator import normalize
from .facts import PATTERNS
from .schemas import Page

ChangeType = Literal["added", "removed", "modified", "unchanged"]


class ClauseDiff(BaseModel):
    change_type: ChangeType
    title: str
    before_text: str | None = None
    after_text: str | None = None
    page_before: int | None = None
    page_after: int | None = None
    significance_note: str | None = None
    is_formatting_only: bool = False
    is_reordered: bool = False


class ComparisonResult(BaseModel):
    doc_a_id: str
    doc_a_name: str
    doc_b_id: str
    doc_b_name: str
    total_changes: int
    added_count: int
    removed_count: int
    modified_count: int
    unchanged_count: int
    formatting_only_count: int
    changes: list[ClauseDiff] = Field(default_factory=list)
    summary: str
    limitations: list[str] = Field(default_factory=list)


class _Section:
    def __init__(self, raw: str, page: int, index: int):
        self.raw = raw.strip()
        self.page = page
        self.index = index
        self.normalized = normalize(self.raw)
        # First 40 chars or first line as title
        first_line = self.raw.split("\n")[0].strip()
        self.title = first_line[:60] if len(first_line) > 5 else f"Clause {index + 1}"


def _split_into_sections(pages: Sequence[Page]) -> list[_Section]:
    """Split pages into distinct paragraphs/clauses while preserving page references."""
    sections: list[_Section] = []
    idx = 0
    for page in pages:
        paragraphs = re.split(r"\n\s*\n+", page.text)
        for p in paragraphs:
            cleaned = p.strip()
            if len(cleaned) >= 15:  # Skip tiny headers/footers
                sections.append(_Section(raw=cleaned, page=page.number, index=idx))
                idx += 1
    return sections


def _find_entity_changes(text_a: str, text_b: str) -> list[str]:
    """Detect specific changes in key legal entities (amounts, dates, durations)."""
    notes: list[str] = []
    for label, pattern in PATTERNS.items():
        vals_a = [m.group().strip() for m in pattern.finditer(text_a)]
        vals_b = [m.group().strip() for m in pattern.finditer(text_b)]
        if vals_a != vals_b and (vals_a or vals_b):
            if vals_a and vals_b:
                notes.append(f"{label.capitalize()} changed from '{', '.join(vals_a)}' to '{', '.join(vals_b)}'")
            elif vals_a and not vals_b:
                notes.append(f"{label.capitalize()} '{', '.join(vals_a)}' removed")
            elif not vals_a and vals_b:
                notes.append(f"{label.capitalize()} '{', '.join(vals_b)}' added")
    return notes


def _strip_punct(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text).strip()


def _is_fmt_only(text_a: str, text_b: str) -> bool:
    norm_a = normalize(text_a)
    norm_b = normalize(text_b)
    if norm_a == norm_b:
        return True
    return _strip_punct(norm_a) == _strip_punct(norm_b)


def compare_documents(
    doc_a_id: str,
    doc_a_name: str,
    pages_a: Sequence[Page],
    doc_b_id: str,
    doc_b_name: str,
    pages_b: Sequence[Page],
    include_formatting: bool = False,
) -> ComparisonResult:
    """Compare two documents and return a traceable, structured comparison."""
    sections_a = _split_into_sections(pages_a)
    sections_b = _split_into_sections(pages_b)

    norm_a = [s.normalized for s in sections_a]
    norm_b = [s.normalized for s in sections_b]

    # Pre-map identical / near-identical sections across documents to detect reordering
    reordered_pairs: dict[int, int] = {}
    matched_b: set[int] = set()
    for sa in sections_a:
        for sb in sections_b:
            if sb.index in matched_b:
                continue
            if _is_fmt_only(sa.raw, sb.raw) or difflib.SequenceMatcher(None, sa.normalized, sb.normalized).ratio() > 0.85:
                matched_b.add(sb.index)
                if sa.index != sb.index:
                    reordered_pairs[sa.index] = sb.index
                break

    matcher = difflib.SequenceMatcher(None, norm_a, norm_b, autojunk=False)
    opcodes = matcher.get_opcodes()

    diffs: list[ClauseDiff] = []
    added_count = 0
    removed_count = 0
    modified_count = 0
    unchanged_count = 0
    formatting_only_count = 0

    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            for a_idx, b_idx in zip(range(i1, i2), range(j1, j2), strict=True):
                sec_a = sections_a[a_idx]
                sec_b = sections_b[b_idx]
                is_exact = sec_a.raw == sec_b.raw
                is_fmt = _is_fmt_only(sec_a.raw, sec_b.raw) and not is_exact
                if is_fmt:
                    formatting_only_count += 1
                unchanged_count += 1
                is_reordered = sec_a.index in reordered_pairs
                diff = ClauseDiff(
                    change_type="unchanged",
                    title=sec_b.title,
                    before_text=sec_a.raw,
                    after_text=sec_b.raw,
                    page_before=sec_a.page,
                    page_after=sec_b.page,
                    significance_note="Position shifted in document" if is_reordered else "Identical clause",
                    is_formatting_only=is_fmt,
                    is_reordered=is_reordered,
                )
                if include_formatting or not is_fmt:
                    diffs.append(diff)

        elif tag == "replace":
            sub_a = sections_a[i1:i2]
            sub_b = sections_b[j1:j2]
            used_b = set()
            for sa in sub_a:
                best_sim = 0.0
                best_sb = None
                for sb in sub_b:
                    if sb.index in used_b:
                        continue
                    sim = difflib.SequenceMatcher(None, sa.normalized, sb.normalized).ratio()
                    if sim > best_sim:
                        best_sim = sim
                        best_sb = sb

                if best_sb is not None and (best_sim >= 0.45 or _is_fmt_only(sa.raw, best_sb.raw)):
                    used_b.add(best_sb.index)
                    entity_changes = _find_entity_changes(sa.raw, best_sb.raw)
                    is_fmt = _is_fmt_only(sa.raw, best_sb.raw)
                    is_reordered = sa.index in reordered_pairs

                    if is_fmt:
                        formatting_only_count += 1
                        change_type = "unchanged"
                        note = "Position shifted; formatting only" if is_reordered else "Formatting or punctuation change only"
                    else:
                        modified_count += 1
                        change_type = "modified"
                        note = "; ".join(entity_changes) if entity_changes else "Wording modified"

                    diff = ClauseDiff(
                        change_type=change_type,
                        title=best_sb.title,
                        before_text=sa.raw,
                        after_text=best_sb.raw,
                        page_before=sa.page,
                        page_after=best_sb.page,
                        significance_note=note,
                        is_formatting_only=is_fmt,
                        is_reordered=is_reordered,
                    )
                    if include_formatting or not is_fmt:
                        diffs.append(diff)
                else:
                    # Check if sa was reordered elsewhere
                    if sa.index in reordered_pairs:
                        b_target = reordered_pairs[sa.index]
                        target_sec = sections_b[b_target]
                        diffs.append(
                            ClauseDiff(
                                change_type="unchanged",
                                title=sa.title,
                                before_text=sa.raw,
                                after_text=target_sec.raw,
                                page_before=sa.page,
                                page_after=target_sec.page,
                                significance_note=f"Clause relocated to Clause {b_target + 1} (Page {target_sec.page})",
                                is_reordered=True,
                            )
                        )
                    else:
                        removed_count += 1
                        diffs.append(
                            ClauseDiff(
                                change_type="removed",
                                title=sa.title,
                                before_text=sa.raw,
                                page_before=sa.page,
                                significance_note="Clause removed in newer version",
                            )
                        )

            for sb in sub_b:
                if sb.index not in used_b:
                    # Check if sb was reordered from elsewhere in A
                    if any(target == sb.index for target in reordered_pairs.values()):
                        continue
                    added_count += 1
                    diffs.append(
                        ClauseDiff(
                            change_type="added",
                            title=sb.title,
                            after_text=sb.raw,
                            page_after=sb.page,
                            significance_note="New clause inserted",
                        )
                    )

        elif tag == "delete":
            for a_idx in range(i1, i2):
                sec_a = sections_a[a_idx]
                removed_count += 1
                diffs.append(
                    ClauseDiff(
                        change_type="removed",
                        title=sec_a.title,
                        before_text=sec_a.raw,
                        page_before=sec_a.page,
                        significance_note="Clause removed in newer version",
                    )
                )

        elif tag == "insert":
            for b_idx in range(j1, j2):
                sec_b = sections_b[b_idx]
                added_count += 1
                diffs.append(
                    ClauseDiff(
                        change_type="added",
                        title=sec_b.title,
                        after_text=sec_b.raw,
                        page_after=sec_b.page,
                        significance_note="New clause inserted",
                    )
                )

    substantive_changes = added_count + removed_count + modified_count
    summary = (
        f"Compared '{doc_a_name}' vs '{doc_b_name}': {substantive_changes} substantive change(s) found "
        f"({added_count} added, {removed_count} removed, {modified_count} modified). "
        f"{unchanged_count} clause(s) remained unchanged."
    )
    if formatting_only_count > 0 and not include_formatting:
        summary += f" ({formatting_only_count} formatting-only difference(s) suppressed for clarity)."

    limitations = [
        "Clause alignment is based on deterministic textual sequence and lexical similarity.",
        "Significance notes describe detected entity shifts (amounts, dates, durations) and are "
        "not legal interpretations of enforceability.",
        "Consult legal counsel to evaluate the material legal impact of identified changes.",
    ]

    return ComparisonResult(
        doc_a_id=doc_a_id,
        doc_a_name=doc_a_name,
        doc_b_id=doc_b_id,
        doc_b_name=doc_b_name,
        total_changes=substantive_changes,
        added_count=added_count,
        removed_count=removed_count,
        modified_count=modified_count,
        unchanged_count=unchanged_count,
        formatting_only_count=formatting_only_count,
        changes=diffs,
        summary=summary,
        limitations=limitations,
    )
