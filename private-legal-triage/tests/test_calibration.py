"""Tests for confidence calibration scoring and evaluation metrics."""


from src.calibration import (
    calculate_brier_score,
    calculate_expected_calibration_error,
    compute_calibrated_confidence,
)


def test_compute_calibrated_confidence_tiers():
    # High confidence: verified citation, grounded numbers, explicit statement
    c_high = compute_calibrated_confidence(
        citation_status="verified",
        has_ungrounded_figures=False,
        statement_type="explicit",
        retrieval_score=2.0,
    )
    assert c_high.tier == "high"
    assert c_high.score >= 0.85
    assert c_high.citation_verified is True
    assert c_high.figures_grounded is True

    # Medium confidence: verified but interpretive reading
    c_med = compute_calibrated_confidence(
        citation_status="verified",
        has_ungrounded_figures=False,
        statement_type="interpretation",
        retrieval_score=0.5,
    )
    assert c_med.tier == "medium"
    assert 0.50 <= c_med.score < 0.85

    # Low confidence: unverified citation
    c_low = compute_calibrated_confidence(
        citation_status="unverified",
        has_ungrounded_figures=False,
        statement_type="explicit",
        retrieval_score=1.0,
    )
    assert c_low.tier == "low"
    assert c_low.score < 0.50
    assert c_low.citation_verified is False


def test_brier_score_calculation():
    # Perfect calibration
    perfect = calculate_brier_score([1.0, 0.0, 1.0], [True, False, True])
    assert perfect == 0.0

    # Intermediate calibration
    intermediate = calculate_brier_score([0.8, 0.2], [True, False])
    # (0.8 - 1)^2 = 0.04, (0.2 - 0)^2 = 0.04 -> mean = 0.04
    assert intermediate == 0.04


def test_ece_calculation():
    preds = [0.9, 0.8, 0.7, 0.4, 0.2]
    truth = [True, True, True, False, False]
    ece = calculate_expected_calibration_error(preds, truth, num_bins=2)
    assert 0.0 <= ece <= 1.0
