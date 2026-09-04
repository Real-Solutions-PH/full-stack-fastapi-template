"""Application-level encryption at rest for connection-secret config blobs.

Connection config for MCP servers and tools can hold bearer tokens, API keys
and auth headers. It is write-only at the API boundary (never echoed) and it is
encrypted at rest here so a database dump alone never exposes a secret.

Scheme: Fernet (AES-128-CBC + HMAC-SHA256, authenticated) over the JSON
serialization of the config dict. ``CONFIG_ENCRYPTION_KEYS`` is a
comma-separated list of urlsafe-base64 Fernet keys; the first encrypts, every
key can decrypt, so a key is rotated by prepending the new one and letting old
blobs re-encrypt on their next write — no bulk re-encrypt pass needed
(``MultiFernet``).

This is a deliberate step below the constitution's envelope-encryption ideal
(a per-tenant data key with the master key in a KMS/Supabase Vault): these
catalogs are global and have no tenant key, and no KMS is wired. The residual
gap is recorded as an ADR. Generate a key with::

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

import json
from typing import Any

from cryptography.fernet import Fernet, MultiFernet
from sqlalchemy import LargeBinary
from sqlalchemy.types import TypeDecorator

# A valid Fernet key used ONLY when ENVIRONMENT=local and CONFIG_ENCRYPTION_KEYS
# is unset, so dev and tests work out of the box. It is public (it lives here),
# protects nothing real, and Settings refuses to fall back to it outside local.
_DEV_KEY = "OFyzG3l-nLnfScZSkaOtDsJtK_gFkbydy4F-AJLgNHc="


def _cipher() -> MultiFernet:
    # Imported lazily so this module has no import-time dependency on settings
    # (and so a test can point the key list somewhere else via the env first).
    from app.core.config import settings

    raw = settings.CONFIG_ENCRYPTION_KEYS.strip()
    keys = [k.strip() for k in raw.split(",") if k.strip()] or [_DEV_KEY]
    return MultiFernet([Fernet(k.encode()) for k in keys])


def encrypt_json(data: dict[str, Any]) -> bytes:
    """Serialize ``data`` to JSON and encrypt it. Returns a Fernet token."""
    return _cipher().encrypt(json.dumps(data, separators=(",", ":")).encode())


def decrypt_json(token: bytes) -> dict[str, Any]:
    """Decrypt a Fernet token produced by :func:`encrypt_json` back to a dict."""
    decoded: dict[str, Any] = json.loads(_cipher().decrypt(bytes(token)).decode())
    return decoded


class EncryptedJSON(TypeDecorator[dict[str, Any]]):
    """A JSON dict column stored as an encrypted opaque blob (``bytea``).

    Transparent to the ORM: assign/read a plain ``dict``; the ciphertext never
    surfaces in Python. Because the stored form is a Fernet token, the column
    cannot be queried or indexed by its contents — which is fine, this config
    is only ever fetched whole by primary key.
    """

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(
        self, value: dict[str, Any] | None, dialect: object
    ) -> bytes | None:
        if value is None:
            return None
        return encrypt_json(value)

    def process_result_value(
        self, value: bytes | None, dialect: object
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        return decrypt_json(value)
