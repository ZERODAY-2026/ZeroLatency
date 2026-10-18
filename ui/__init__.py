"""UI package for Redline Private Legal Triage.

Ensures the backend package (private-legal-triage) is in sys.path.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "private-legal-triage"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
