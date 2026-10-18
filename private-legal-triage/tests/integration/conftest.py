import json
import os
import time
from pathlib import Path

import pytest

REPORT = Path(__file__).resolve().parents[2] / "reports" / "real_model_run.json"


def pytest_collection_modifyitems(config, items):
    if os.getenv("TRIAGE_RUN_REAL_MODEL") == "1":
        return
    skip = pytest.mark.skip(reason="opt-in: set TRIAGE_RUN_REAL_MODEL=1 (needs Ollama + a Gemma 3n model)")
    for item in items:
        if "real_model" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def run_log():
    """Collects measured values; written to reports/real_model_run.json when the session ends."""
    log: dict = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "results": {}}
    yield log
    if log["results"]:
        REPORT.parent.mkdir(exist_ok=True)
        REPORT.write_text(json.dumps(log, indent=2), encoding="utf-8")
