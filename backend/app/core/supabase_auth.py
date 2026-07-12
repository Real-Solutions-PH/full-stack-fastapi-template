"""Supabase Auth integration (#39).

Two concerns live here:

* **Token verification** — validate Supabase-issued access tokens against
  the project's JWKS (same path for the local CLI stack and hosted
  projects). The JWK client caches keys at module scope.
* **GoTrue admin helpers** — create/look-up auth users with the
  service-role key. Used by the FIRST_SUPERUSER bootstrap, the local-only
  ``/private/users`` route, superuser user creation, and test fixtures.
"""

import uuid
from typing import Any

import httpx
import jwt
from jwt import PyJWKClient

from app.core.config import settings

AUDIENCE = "authenticated"

# Module-scope JWKS client: caches signing keys across requests.
_jwk_client: PyJWKClient | None = None


def _get_jwk_client() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(
            settings.supabase_jwks_url, cache_keys=True, lifespan=300
        )
    return _jwk_client


def verify_token(token: str) -> dict[str, Any]:
    """Validate a Supabase access token and return its claims.

    Checks signature (via JWKS), ``exp``, ``aud`` ("authenticated") and
    ``iss`` (the Supabase auth endpoint). Raises ``jwt.PyJWTError`` (or a
    subclass) on any failure — including JWKS fetch/key-lookup errors.
    """
    signing_key = _get_jwk_client().get_signing_key_from_jwt(token)
    claims: dict[str, Any] = jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256", "RS256"],
        audience=AUDIENCE,
        issuer=settings.supabase_issuer,
        options={"require": ["exp", "sub", "aud", "iss"]},
    )
    return claims


# --------------------------------------------------------------------------
# GoTrue admin API (service-role key; backend-only)
# --------------------------------------------------------------------------


def _admin_headers() -> dict[str, str]:
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    return {"Authorization": f"Bearer {key}", "apikey": key}


def _auth_url(path: str) -> str:
    return f"{settings.SUPABASE_URL}/auth/v1{path}"


def admin_get_user_id_by_email(email: str) -> uuid.UUID | None:
    """Return the auth UID for an existing GoTrue user, or None.

    GoTrue's admin list endpoint has no email filter, but
    ``/admin/generate_link`` (type=magiclink) returns the full user object
    for an existing email without sending anything.
    """
    r = httpx.post(
        _auth_url("/admin/generate_link"),
        headers=_admin_headers(),
        json={"type": "magiclink", "email": email},
        timeout=10,
    )
    if r.status_code == 200:
        return uuid.UUID(r.json()["id"])
    if r.status_code in (404, 422):
        return None
    r.raise_for_status()
    return None  # pragma: no cover - raise_for_status always raises here


def admin_get_or_create_user(email: str, password: str | None = None) -> uuid.UUID:
    """Idempotently ensure a GoTrue user exists; return its auth UID.

    If the user already exists and ``password`` is given, the password is
    reset so callers (bootstrap, test fixtures) end in a known state.
    """
    body: dict[str, Any] = {"email": email, "email_confirm": True}
    if password is not None:
        body["password"] = password
    r = httpx.post(
        _auth_url("/admin/users"), headers=_admin_headers(), json=body, timeout=10
    )
    if r.status_code == 200:
        return uuid.UUID(r.json()["id"])
    if r.status_code == 422 and r.json().get("error_code") == "email_exists":
        user_id = admin_get_user_id_by_email(email)
        if user_id is None:  # pragma: no cover - create/lookup race
            raise RuntimeError(f"GoTrue reports {email} exists but lookup failed")
        if password is not None:
            httpx.put(
                _auth_url(f"/admin/users/{user_id}"),
                headers=_admin_headers(),
                json={"password": password},
                timeout=10,
            ).raise_for_status()
        return user_id
    r.raise_for_status()
    raise RuntimeError("unreachable")  # pragma: no cover
