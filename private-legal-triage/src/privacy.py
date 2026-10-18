import gc
import ipaddress
import os
import shutil
import socket
import tempfile
import threading
import time
import uuid
from contextlib import contextmanager, suppress
from pathlib import Path
from urllib.parse import urlparse

from .errors import PrivacyViolation

LOCAL_NAMES = {"localhost"}


def is_loopback_host(host: str) -> bool:
    host = host.strip("[]")
    if host.lower() in LOCAL_NAMES:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def assert_loopback_url(url: str) -> str:
    host = urlparse(url).hostname
    if not host or not is_loopback_host(host):
        raise PrivacyViolation("Only loopback model endpoints are allowed for document processing.")
    return url.rstrip("/")


_GUARD_DEPTH = 0
_GUARD_LOCK = threading.Lock()
_ORIGINAL_CONNECT = socket.socket.connect
_ORIGINAL_CONNECT_EX = socket.socket.connect_ex
_ORIGINAL_GETADDRINFO = socket.getaddrinfo
_ORIGINAL_SENDTO = socket.socket.sendto


@contextmanager
def network_guard(observed: list[str] | None = None):
    """Python-level guard: blocks non-loopback connect/DNS/sendto made through the socket module.

    Limits: it does not see native code that opens sockets itself, other processes (including
    Ollama), or subprocesses. Use OS-level isolation for stronger evidence (see docs/PRIVACY.md).
    `observed`, if given, collects every host checked (allowed or blocked).
    """
    global _GUARD_DEPTH
    blocked: list[str] = []

    def check(host) -> None:
        if isinstance(host, bytes):
            host = host.decode(errors="ignore")
        if observed is not None:
            observed.append(str(host))
        if host in (None, "") or is_loopback_host(str(host)):
            return
        blocked.append(str(host))
        raise PrivacyViolation(f"Blocked outbound network access to {host}")

    def guarded_connect(self, address):
        if isinstance(address, tuple):
            check(address[0])
        return _ORIGINAL_CONNECT(self, address)

    def guarded_connect_ex(self, address):
        if isinstance(address, tuple):
            check(address[0])
        return _ORIGINAL_CONNECT_EX(self, address)

    def guarded_getaddrinfo(host, *args, **kwargs):
        check(host)
        return _ORIGINAL_GETADDRINFO(host, *args, **kwargs)

    def guarded_sendto(self, data, *args):
        address = args[-1] if args else None
        if isinstance(address, tuple):
            check(address[0])
        return _ORIGINAL_SENDTO(self, data, *args)

    with _GUARD_LOCK:
        if _GUARD_DEPTH == 0:
            socket.socket.connect = guarded_connect
            socket.socket.sendto = guarded_sendto
            socket.socket.connect_ex = guarded_connect_ex
            socket.getaddrinfo = guarded_getaddrinfo
        _GUARD_DEPTH += 1

    try:
        yield blocked
    finally:
        with _GUARD_LOCK:
            _GUARD_DEPTH -= 1
            if _GUARD_DEPTH == 0:
                socket.socket.connect = _ORIGINAL_CONNECT
                socket.socket.sendto = _ORIGINAL_SENDTO
                socket.socket.connect_ex = _ORIGINAL_CONNECT_EX
                socket.getaddrinfo = _ORIGINAL_GETADDRINFO


class PrivateWorkspace:
    def __init__(self) -> None:
        self.root: Path | None = None

    def __enter__(self) -> "PrivateWorkspace":
        self.root = Path(tempfile.mkdtemp(prefix="triage_"))
        # os.chmod 0o700 restricts POSIX systems; it is a no-op on Windows where
        # directory access is governed by ACLs rather than POSIX mode bits.
        os.chmod(self.root, 0o700)
        return self

    def save_upload(self, filename: str, data: bytes) -> Path:
        if self.root is None:
            raise RuntimeError("Workspace is not open")
        suffix = Path(filename).suffix.lower()
        target = self.root / f"{uuid.uuid4().hex}{suffix}"
        target.write_bytes(data)
        os.chmod(target, 0o600)
        return target

    def delete_file(self, path: Path) -> None:
        """Best-effort overwrite then unlink. Not a guarantee on SSDs or journaling filesystems."""
        _overwrite_and_remove(Path(path))

    def cleanup(self) -> None:
        if self.root is None or not self.root.exists():
            return
        for path in self.root.rglob("*"):
            if path.is_file():
                _overwrite_and_remove(path, remove=False)
        shutil.rmtree(self.root, ignore_errors=True)
        self.root = None

    def __exit__(self, *exc) -> None:
        self.cleanup()


def _overwrite_and_remove(path: Path, remove: bool = True) -> None:
    try:
        if path.is_file():
            size = path.stat().st_size
            with path.open("r+b") as handle:
                handle.write(b"\0" * size)
                handle.flush()
                os.fsync(handle.fileno())
    except OSError:
        pass
    if remove:
        _unlink_with_retry(path)


def _unlink_with_retry(path: Path, *, retries: int = 5, delay: float = 0.1) -> None:
    """Unlink with retry for Windows: C-extension handles (e.g. PyMuPDF) may be
    held in native code and are released lazily by the GC rather than deterministically.
    Runs gc.collect() before retrying to encourage handle release.
    """
    for attempt in range(retries + 1):
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError:
            if attempt < retries:
                gc.collect()
                time.sleep(delay)
    # Last attempt: best-effort; the file may linger until the process exits.
    with suppress(PermissionError):
        path.unlink(missing_ok=True)

