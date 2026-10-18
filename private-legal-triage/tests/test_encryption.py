"""Tests for local at-rest encryption and secure ephemeral key handling."""

import os

import pytest

from src.encryption import (
    EphemeralKey,
    decrypt_data,
    encrypt_data,
)
from src.privacy import PrivateWorkspace


def test_encryption_roundtrip():
    key = EphemeralKey()
    key_bytes = key.get_bytes()
    original_text = b"Secret contract clause: Tenant pays deposit of Rs. 50,000 to Landlord."

    ciphertext = encrypt_data(original_text, key_bytes)
    assert ciphertext != original_text
    assert b"Tenant pays deposit" not in ciphertext

    decrypted = decrypt_data(ciphertext, key_bytes)
    assert decrypted == original_text

    key.zeroize()


def test_zeroized_key_cannot_decrypt():
    key = EphemeralKey()
    key_bytes = key.get_bytes()
    data = b"Confidential financial statement and bank guarantee."

    ciphertext = encrypt_data(data, key_bytes)

    # Key zeroized
    key.zeroize()
    with pytest.raises(RuntimeError):
        key.get_bytes()

    # Attempting to decrypt with a different random key fails authentication
    wrong_key = os.urandom(32)
    from cryptography.exceptions import InvalidTag
    with pytest.raises(InvalidTag):
        decrypt_data(ciphertext, wrong_key)


def test_encrypted_workspace_lifecycle(tmp_path):
    with PrivateWorkspace(encrypt_at_rest=True) as ws:
        original_data = b"Highly confidential lease agreement terms."
        path = ws.save_upload("lease.txt", original_data)

        # Raw file on disk MUST be encrypted ciphertext, NOT plaintext
        raw_disk = path.read_bytes()
        assert raw_disk != original_data
        assert b"Highly confidential" not in raw_disk

        # Reading via workspace decrypts seamlessly with in-memory ephemeral key
        recovered = ws.read_upload(path)
        assert recovered == original_data

        ws_root = ws.root
        assert ws_root.exists()

    # After exit/cleanup, directory is removed and key is zeroized
    assert not ws_root.exists()
    assert ws._key is None
