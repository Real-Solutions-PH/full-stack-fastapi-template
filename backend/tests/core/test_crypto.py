"""Application-level encryption for connection-secret config blobs.

Proves the primitive that keeps MCP/tool ``config`` opaque at rest: a
symmetric authenticated cipher (Fernet), JSON in / JSON out, with a
comma-separated key list so a key can be rotated without a re-encrypt pass.
"""

import json

import pytest
from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.core import crypto


def test_round_trips_a_dict() -> None:
    data = {"auth_token": "S3CR3T", "headers": {"X-Api-Key": "abc"}}
    assert crypto.decrypt_json(crypto.encrypt_json(data)) == data


def test_round_trips_an_empty_dict() -> None:
    assert crypto.decrypt_json(crypto.encrypt_json({})) == {}


def test_ciphertext_does_not_contain_plaintext_secret() -> None:
    token = crypto.encrypt_json({"auth_token": "S3CR3T"})
    assert b"S3CR3T" not in token
    assert b"auth_token" not in token


def test_encryption_is_non_deterministic() -> None:
    # Fernet embeds a random IV + timestamp, so the same plaintext encrypts to
    # different ciphertexts — no equality oracle on the stored blob.
    data = {"auth_token": "S3CR3T"}
    assert crypto.encrypt_json(data) != crypto.encrypt_json(data)


def test_tampered_ciphertext_is_rejected() -> None:
    token = bytearray(crypto.encrypt_json({"auth_token": "S3CR3T"}))
    token[-1] ^= 0x01  # flip a bit
    with pytest.raises(InvalidToken):
        crypto.decrypt_json(bytes(token))


def test_key_rotation_decrypts_old_ciphertext() -> None:
    # A blob written under the previous key must still decrypt once a new key
    # is prepended as primary — this is exactly MultiFernet's contract, which
    # ``crypto`` uses when CONFIG_ENCRYPTION_KEYS holds more than one key.
    old_key = Fernet.generate_key()
    new_key = Fernet.generate_key()
    old_blob = Fernet(old_key).encrypt(json.dumps({"k": "v"}).encode())

    rotated = MultiFernet([Fernet(new_key), Fernet(old_key)])
    assert json.loads(rotated.decrypt(old_blob)) == {"k": "v"}
    # and new writes use the primary (new) key, which the old cipher can't read
    new_blob = rotated.encrypt(b"{}")
    with pytest.raises(InvalidToken):
        Fernet(old_key).decrypt(new_blob)
