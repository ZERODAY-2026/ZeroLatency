"""Local-first encryption module for data-at-rest protection.

Threat Model:
An attacker with unauthorized physical access to the device or local filesystem
could attempt low-level block recovery on residual disk blocks or temporary files.

Design & Guarantees:
1. Dynamic Key Generation: Session encryption keys are generated dynamically at runtime
   via os.urandom / secrets.token_bytes(32) CSPRNG. Keys are NEVER hardcoded and NEVER
   written to disk beside the ciphertext.
2. Authenticated Encryption: Uses standard AES-256-GCM authenticated encryption. Each write
   uses a unique cryptographically random 96-bit (12-byte) initialization nonce.
3. Volatile Key Lifecycle: Keys exist only in RAM during the active workspace session.
   Upon session closure, keys are zeroized in memory. Without the key, any residual
   NAND flash blocks or filesystem artifacts cannot be decrypted.
"""

import os
import secrets
from typing import Final

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_BYTES: Final[int] = 12
KEY_BYTES: Final[int] = 32


class EphemeralKey:
    """In-memory symmetric key that is zeroized on disposal."""

    def __init__(self) -> None:
        self._key: bytearray | None = bytearray(secrets.token_bytes(KEY_BYTES))

    def get_bytes(self) -> bytes:
        if self._key is None:
            raise RuntimeError("Encryption key has already been wiped from memory.")
        return bytes(self._key)

    def zeroize(self) -> None:
        if self._key is not None:
            for i in range(len(self._key)):
                self._key[i] = 0
            self._key = None

    def __del__(self) -> None:
        self.zeroize()


def encrypt_data(data: bytes, key: bytes) -> bytes:
    """Encrypt data using AES-256-GCM with a fresh random nonce.

    Returns: nonce (12 bytes) + ciphertext + authentication tag (16 bytes).
    """
    if len(key) != KEY_BYTES:
        raise ValueError(f"AES-256 key must be exactly {KEY_BYTES} bytes.")
    nonce = os.urandom(NONCE_BYTES)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce + ciphertext


def decrypt_data(encrypted_payload: bytes, key: bytes) -> bytes:
    """Decrypt payload using AES-256-GCM.

    Expects: nonce (12 bytes) + ciphertext + authentication tag.
    Raises ValueError / InvalidTag if authentication fails or payload is corrupt.
    """
    if len(key) != KEY_BYTES:
        raise ValueError(f"AES-256 key must be exactly {KEY_BYTES} bytes.")
    if len(encrypted_payload) < NONCE_BYTES + 16:
        raise ValueError("Encrypted payload is shorter than minimum nonce + tag size.")
    nonce = encrypted_payload[:NONCE_BYTES]
    ciphertext = encrypted_payload[NONCE_BYTES:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)
