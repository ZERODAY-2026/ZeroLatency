import re
import socket
from pathlib import Path

import pytest

from src.errors import PrivacyViolation
from src.privacy import PrivateWorkspace, assert_loopback_url, network_guard

SRC = Path(__file__).resolve().parents[1] / "src"
FORBIDDEN_IMPORTS = ("openai", "anthropic", "google.generativeai", "boto3", "httpx", "sentry_sdk")


def test_guard_blocks_external_connect():
    with network_guard() as blocked:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with pytest.raises(PrivacyViolation):
            sock.connect(("93.184.216.34", 80))
        sock.close()
    assert blocked == ["93.184.216.34"]


def test_guard_blocks_dns_lookup():
    with network_guard(), pytest.raises(PrivacyViolation):
        socket.getaddrinfo("example.com", 80)


def test_guard_allows_loopback():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    with network_guard() as blocked:
        client = socket.create_connection(("127.0.0.1", port), timeout=2)
        client.close()
    server.close()
    assert blocked == []


def test_guard_is_removed_afterwards():
    original = socket.socket.connect
    with network_guard():
        assert socket.socket.connect is not original
    assert socket.socket.connect is original


def test_loopback_url_enforced():
    assert assert_loopback_url("http://127.0.0.1:11434/") == "http://127.0.0.1:11434"
    assert assert_loopback_url("http://localhost:11434") == "http://localhost:11434"
    for url in ("https://api.example.com", "http://192.168.1.5:11434", "http://0.0.0.0:11434"):
        with pytest.raises(PrivacyViolation):
            assert_loopback_url(url)


def test_workspace_cleans_up():
    import platform

    with PrivateWorkspace() as ws:
        saved = ws.save_upload("contract.PDF", b"secret")
        root = ws.root
        assert saved.suffix == ".pdf" and saved.read_bytes() == b"secret"
        # POSIX permission bits are not enforced by Windows; os.chmod is a no-op there.
        if platform.system() != "Windows":
            assert (root.stat().st_mode & 0o777) == 0o700
    assert not root.exists()


def test_source_has_no_hosted_sdks_or_remote_urls():
    for path in SRC.glob("*.py"):
        text = path.read_text()
        for name in FORBIDDEN_IMPORTS:
            assert not re.search(rf"^\s*(?:import|from)\s+{re.escape(name)}\b", text, re.M), (path.name, name)
        for url in re.findall(r"https?://[^\s\"')]+", text):
            assert re.match(r"https?://(?:127\.0\.0\.1|localhost)\b", url), (path.name, url)


NETWORK_MODULES = ("subprocess", "urllib.request", "http.client", "ftplib", "smtplib", "telnetlib", "websocket")


def test_source_has_no_subprocess_or_extra_network_modules():
    for path in SRC.glob("*.py"):
        text = path.read_text()
        for name in NETWORK_MODULES:
            assert not re.search(rf"^\s*(?:import|from)\s+{re.escape(name)}\b", text, re.M), (path.name, name)
        assert "os.system" not in text and "os.popen" not in text, path.name


def test_only_the_model_client_and_privacy_module_touch_the_network_stack():
    allowed = {"gemma_client.py": "requests", "privacy.py": "socket"}
    for path in SRC.glob("*.py"):
        text = path.read_text()
        for module in ("requests", "socket"):
            uses = re.search(rf"^\s*(?:import|from)\s+{module}\b", text, re.M)
            assert not uses or allowed.get(path.name) == module, (path.name, module)


def test_no_logging_of_document_data_in_library_code():
    for path in SRC.glob("*.py"):
        if path.name == "cli.py":
            continue
        text = path.read_text()
        assert not re.search(r"^\s*(?:import logging|from logging)", text, re.M), path.name
        assert "print(" not in text, path.name
