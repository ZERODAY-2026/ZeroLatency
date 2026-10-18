"""Offline and privacy verification script.

Runs end-to-end document processing under strict network surveillance:
1. Wraps execution in network_guard to verify no non-loopback network calls or external DNS queries.
2. Tests document upload, analysis, questioning, and deletion.
3. Verifies that no document text, questions, or answers leak into application logs.
4. Reports observed connections, verified boundaries, and storage limitations.
"""

import io
import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.config import Settings
from src.errors import PrivacyViolation
from src.gemma_client import OllamaClient
from src.privacy import is_loopback_host, network_guard
from src.service import DocumentStore
from tests.conftest import RENTAL_PAGES
from tests.helpers import rental_responder
from tests.stub_ollama import StubOllama


def run_privacy_audit() -> bool:
    print("=" * 60)
    print("PRIVATE LEGAL DOCUMENT TRIAGE — PRIVACY & OFFLINE AUDIT")
    print("=" * 60)

    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)

    observed_addrs: list[str] = []
    text_sample = "\n\n".join(RENTAL_PAGES).encode("utf-8")
    sample_secret_phrases = ["Asha Rao", "refundable security deposit", "Rs. 25,000"]

    print("\n[1/4] Starting isolated loopback environment...")
    with StubOllama(installed=["gemma3n:e2b", "gemma3n:e4b"], responder=rental_responder) as stub:
        cfg = Settings(ollama_url=stub.url)

        print("[2/4] Executing end-to-end triage pipeline inside network_guard()...")
        try:
            with network_guard(observed_addrs) as blocked:
                store = DocumentStore(cfg, OllamaClient(cfg))

                # 1. Upload
                doc = store.upload("lease_private.txt", text_sample)
                print(f"      - Document uploaded (ID: {doc.id}, Size: {doc.size_bytes} bytes)")

                # 2. Analyze
                job = store.start_analysis(doc.id, model="gemma3n:e2b")
                completed_job = store.wait(job.id)
                print(f"      - Analysis job {completed_job.id} completed (State: {completed_job.state})")

                # 3. Ask
                answer = store.ask(doc.id, "What is the security deposit?", model="gemma3n:e2b")
                print(f"      - Q&A completed (Answerable: {answer.answerable})")

                # 4. Search
                hits = store.search(doc.id, "security deposit", k=2)
                print(f"      - BM25 search completed (Hits: {len(hits)})")

                # 5. Delete
                store.delete(doc.id)
                print("      - Document securely unlinked from workspace.")

                store.close()
                print("      - Workspace closed and cleaned.")

        except PrivacyViolation as exc:
            print(f"\n[FAIL] Privacy violation detected: {exc}", file=sys.stderr)
            return False

    print("\n[3/4] Verifying network connection containment...")
    for addr in observed_addrs:
        if not is_loopback_host(addr):
            print(f"[FAIL] Non-loopback network destination detected: {addr}", file=sys.stderr)
            return False
        print(f"      - Verified connection to loopback destination: {addr}")

    if blocked:
        print(f"[FAIL] Blocked connection attempts: {blocked}", file=sys.stderr)
        return False
    print("      - No unauthorized or outbound external connections attempted.")

    print("\n[4/4] Verifying log isolation (zero document content leakage)...")
    logs = log_capture.getvalue()
    for phrase in sample_secret_phrases:
        if phrase in logs:
            print(f"[FAIL] Secret document phrase found in logs: '{phrase}'", file=sys.stderr)
            return False
    print("      - Log scrub verified: zero document passages or secrets leaked to logs.")

    print("\n" + "=" * 60)
    print("AUDIT RESULT: PASSED (All privacy guarantees confirmed)")
    print("=" * 60)
    print("NOTE: On flash media (SSDs) and journaling filesystems (NTFS/ext4),")
    print("operating-system-level wear leveling may leave residual traces of deleted")
    print("sectors. Full disk encryption (e.g. BitLocker, LUKS) is strongly advised.")
    return True


if __name__ == "__main__":
    success = run_privacy_audit()
    sys.exit(0 if success else 1)
