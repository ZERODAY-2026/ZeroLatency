import json

from tests.conftest import analysis_json, finding

SUMMARY = json.dumps({"summary": "A short residential lease."})
ANSWER = json.dumps(
    {
        "answerable": True,
        "answer": "The deposit is Rs. 75,000 and refundable.",
        "evidence_quotes": ["refundable security deposit of Rs. 75,000"],
        "statement_type": "explicit",
        "jurisdiction_dependent": False,
    }
)
RENT_QUOTE = "monthly rent of Rs. 25,000 on or before the 5th day of each month"


def rental_responder(model, system, user):
    """Deterministic stand-in for a model, keyed on the prompt. Used only with the stub server."""
    if user.startswith("Section notes"):
        return SUMMARY
    if user.startswith("Question:"):
        return ANSWER
    if "2. RENT" in user:
        return analysis_json([finding(RENT_QUOTE)])
    return analysis_json()
