"""Tests for malformed document handling, error propagation, and privacy boundaries."""

import pytest
from fastapi.testclient import TestClient

from src.api import create_app
from src.config import Settings
from src.errors import (
    LimitExceeded,
    UnreadableDocument,
    UnsupportedFormat,
)
from src.service import DocumentStore


def test_empty_file_rejected():
    store = DocumentStore()
    with pytest.raises(UnreadableDocument):
        store.upload("empty.txt", b"")
    store.close()


def test_unsupported_file_extension_rejected():
    store = DocumentStore()
    with pytest.raises(UnsupportedFormat):
        store.upload("contract.docx", b"PK fake word doc contents")
    with pytest.raises(UnsupportedFormat):
        store.upload("image.png", b"\x89PNG\r\n\x1a\nfake")
    store.close()


def test_oversized_file_rejected():
    store = DocumentStore(Settings(max_file_bytes=1000))
    with pytest.raises(LimitExceeded):
        store.upload("huge.txt", b"A" * 1001)
    store.close()


def test_corrupted_pdf_stream_rejected():
    store = DocumentStore()
    with pytest.raises(UnreadableDocument):
        store.upload("broken.pdf", b"%PDF-1.4 corrupt data not a real pdf %%EOF")
    store.close()


def test_error_responses_contain_no_document_secrets_in_api():
    secret_term = "CONFIDENTIAL_MERGER_PROJECT_TITAN_7788"
    secret_file = f"The terms of {secret_term} are strictly secret.\x00invalid binary chars\xff".encode("latin-1")

    store = DocumentStore()
    app = create_app(store)

    with TestClient(app) as client:
        # Uploading corrupted text file
        resp = client.post(
            "/documents",
            files={"file": ("corrupt.txt", secret_file, "text/plain")},
        )
        assert resp.status_code == 422
        body = resp.text
        # Secrets MUST NOT leak into error responses
        assert secret_term not in body
        assert "UnreadableDocument" in body

    store.close()


def test_cleanup_runs_even_after_failed_uploads(tmp_path):
    store = DocumentStore()
    workspace_path = store._workspace.root

    # Try uploading corrupt file
    with pytest.raises(UnreadableDocument):
        store.upload("bad.pdf", b"corrupted bytes")

    # Verify no leaked residual file remains in workspace
    files = list(workspace_path.glob("*"))
    assert len(files) == 0

    store.close()
