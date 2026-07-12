"""Supabase Auth integration tests (#39).

These run against the local Supabase stack (`make supabase-up`): tokens are
real GoTrue-issued ES256 JWTs verified through the JWKS endpoint.
"""

import uuid

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core import supabase_auth
from app.core.config import settings
from app.core.db import init_db
from app.db.models import User
from app.modules.iam.tenants import services as tenant_service
from tests.utils.utils import (
    auth_headers,
    random_email,
    random_lower_string,
    supabase_password_grant,
)


def test_verify_token_accepts_real_gotrue_token(db: Session) -> None:
    token = supabase_password_grant(
        settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )
    claims = supabase_auth.verify_token(token)
    assert claims["aud"] == "authenticated"
    assert claims["email"] == settings.FIRST_SUPERUSER
    assert claims["iss"] == settings.supabase_issuer
    # sub is the auth UID and must equal the bootstrapped local PK
    user = db.get(User, uuid.UUID(claims["sub"]))
    assert user is not None
    assert user.is_superuser


def test_verify_token_rejects_tampered_token() -> None:
    token = supabase_password_grant(
        settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )
    with pytest.raises(jwt.PyJWTError):
        supabase_auth.verify_token(token[:-3] + "xxx")


def test_garbage_bearer_token_is_403(client: TestClient) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert r.status_code == 403
    assert r.json()["message"] == "Could not validate credentials"


def test_jit_provisioning_creates_local_mirror_row(
    client: TestClient, db: Session
) -> None:
    """First authenticated request from a Supabase-only user creates the
    local row: id == auth UID, default tenant, active, not superuser."""
    email = random_email()
    password = random_lower_string()
    auth_uid = supabase_auth.admin_get_or_create_user(email=email, password=password)
    assert db.get(User, auth_uid) is None

    r = client.get(
        f"{settings.API_V1_STR}/users/me", headers=auth_headers(email, password)
    )
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == email
    assert body["id"] == str(auth_uid)

    user = db.get(User, auth_uid)
    assert user is not None
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.tenant_id == tenant_service.get_default_tenant(session=db).id


def test_bootstrap_is_idempotent(db: Session) -> None:
    from sqlmodel import select

    init_db(db)
    init_db(db)
    rows = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).all()
    assert len(rows) == 1
    assert rows[0].is_superuser
    # Auth UID is stable across bootstraps.
    assert rows[0].id == supabase_auth.admin_get_or_create_user(
        email=settings.FIRST_SUPERUSER, password=settings.FIRST_SUPERUSER_PASSWORD
    )
