"""Confidence calibration and evaluation module.

Establishes a principled, evidence-grounded confidence framework:
1. Keeps evidence verification, numerical groundedness, model statement type,
   and retrieval quality as explicitly separate signals.
2. Avoids presenting raw model-generated confidence as a statistical probability of correctness.
3. Maps multi-factor verification signals to calibrated confidence tiers.
4. Provides standard calibration evaluation metrics (Brier Score, ECE).
"""

from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, Field

ConfidenceTier = Literal["high", "medium", "low"]


class CalibratedConfidence(BaseModel):
    tier: ConfidenceTier
    score: float = Field(ge=0.0, le=1.0)
    citation_verified: bool
    figures_grounded: bool
    is_explicit: bool
    retrieval_score: float
    explanation: str
    limitations: list[str] = Field(default_factory=list)


def compute_calibrated_confidence(
    citation_status: str,  # "verified" | "unverified"
    has_ungrounded_figures: bool,
    statement_type: str,   # "explicit" | "interpretation"
    retrieval_score: float = 1.0,
) -> CalibratedConfidence:
    """Calculate calibrated confidence score from explicit verification components."""
    # 1. Citation verification weight (base 0.50)
    cit_score = 0.50 if citation_status == "verified" else 0.0

    # 2. Factual numerical groundedness weight (0.25)
    ground_score = 0.0 if has_ungrounded_figures else 0.25

    # 3. Statement explicitness weight (0.15)
    stmt_score = 0.15 if statement_type == "explicit" else 0.05

    # 4. Retrieval relevance weight (0.10)
    norm_retrieval = min(1.0, max(0.0, retrieval_score / 2.0)) * 0.10

    total_score = round(cit_score + ground_score + stmt_score + norm_retrieval, 2)

    # Determine semantic tier
    if total_score >= 0.85:
        tier: ConfidenceTier = "high"
        reason = "High confidence: citation verified verbatim in source page with zero ungrounded figures."
    elif total_score >= 0.50:
        tier = "medium"
        reason = (
            "Medium confidence: citation verified but involves interpretation or lower retrieval score."
            if citation_status == "verified"
            else "Medium confidence: citation unverified."
        )
    else:
        tier = "low"
        reason = "Low confidence: citation unverified or ungrounded figures detected in explanation."

    limitations = [
        "Calibrated confidence measures evidence traceability and citation grounding.",
        "It does not represent a statistical guarantee of legal correctness or judicial validity.",
    ]

    return CalibratedConfidence(
        tier=tier,
        score=total_score,
        citation_verified=(citation_status == "verified"),
        figures_grounded=(not has_ungrounded_figures),
        is_explicit=(statement_type == "explicit"),
        retrieval_score=round(retrieval_score, 3),
        explanation=reason,
        limitations=limitations,
    )


def calculate_brier_score(predictions: Sequence[float], ground_truth: Sequence[bool]) -> float:
    """Compute Brier Score: mean squared error between calibrated probability and binary outcome."""
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground_truth must have identical lengths.")
    if not predictions:
        return 0.0
    total = sum((p - (1.0 if y else 0.0)) ** 2 for p, y in zip(predictions, ground_truth, strict=True))
    return round(total / len(predictions), 4)


def calculate_expected_calibration_error(
    predictions: Sequence[float],
    ground_truth: Sequence[bool],
    num_bins: int = 5,
) -> float:
    """Compute Expected Calibration Error (ECE) across partitioned probability bins."""
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground_truth must have identical lengths.")
    if not predictions:
        return 0.0

    n = len(predictions)
    ece = 0.0
    for b in range(num_bins):
        bin_lower = b / num_bins
        bin_upper = (b + 1) / num_bins
        bin_items = [
            (p, y)
            for p, y in zip(predictions, ground_truth, strict=True)
            if bin_lower <= p < bin_upper or (b == num_bins - 1 and p == bin_upper)
        ]
        if bin_items:
            bin_size = len(bin_items)
            avg_pred = sum(p for p, _ in bin_items) / bin_size
            avg_acc = sum(1.0 if y else 0.0 for _, y in bin_items) / bin_size
            ece += (bin_size / n) * abs(avg_acc - avg_pred)

    return round(ece, 4)
