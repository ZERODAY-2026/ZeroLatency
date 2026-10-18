import json

import pytest

from samples.make_samples import RENTAL_PAGES, write_pdf


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat_json(self, system, user, schema):
        self.calls.append((system, user))
        item = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        return item(user) if callable(item) else item


def analysis_json(findings=None, summary="Covers the lease term and rent."):
    return json.dumps({"chunk_summary": summary, "findings": findings or []})


def finding(quote, **overrides):
    base = {
        "category": "obligation",
        "title": "Monthly rent",
        "explanation": "The tenant pays Rs. 25,000 each month.",
        "evidence_quote": quote,
        "statement_type": "explicit",
        "jurisdiction_dependent": False,
    }
    base.update(overrides)
    return base


@pytest.fixture
def rental_pdf(tmp_path):
    return write_pdf(tmp_path / "rental.pdf", RENTAL_PAGES)


@pytest.fixture
def rental_txt(tmp_path):
    path = tmp_path / "rental.txt"
    path.write_text("\n\n".join(RENTAL_PAGES), encoding="utf-8")
    return path
