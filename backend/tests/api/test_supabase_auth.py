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


def test_delete_me_revokes_auth_identity_no_resurrection(
    client: TestClient, db: Session
) -> None:
    """DELETE /users/me removes the GoTrue user too, and the same
    still-valid token cannot resurrect the account via JIT provisioning."""
    email = random_email()
    password = random_lower_string()
    auth_uid = supabase_auth.admin_get_or_create_user(email=email, password=password)
    headers = auth_headers(email, password)

    r = client.delete(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 200

    # Auth identity is gone.
    assert supabase_auth.admin_user_exists(auth_uid) is False
    # The token is still signature-valid (< jwt_expiry) but must NOT
    # re-provision a local row: the JIT path checks GoTrue first.
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 401
    assert db.get(User, auth_uid) is None


def test_admin_delete_user_tolerates_already_gone() -> None:
    email = random_email()
    auth_uid = supabase_auth.admin_get_or_create_user(email=email)
    supabase_auth.admin_delete_user(auth_uid)
    # Second delete: GoTrue answers 404, helper swallows it.
    supabase_auth.admin_delete_user(auth_uid)
    assert supabase_auth.admin_user_exists(auth_uid) is False


def test_superuser_delete_revokes_auth_identity(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    email = random_email()
    password = random_lower_string()
    auth_uid = supabase_auth.admin_get_or_create_user(email=email, password=password)
    # Materialize the local mirror row via a first authenticated request.
    r = client.get(
        f"{settings.API_V1_STR}/users/me", headers=auth_headers(email, password)
    )
    assert r.status_code == 200

    r = client.delete(
        f"{settings.API_V1_STR}/users/{auth_uid}", headers=superuser_token_headers
    )
    assert r.status_code == 200
    assert supabase_auth.admin_user_exists(auth_uid) is False
    assert db.get(User, auth_uid) is None


def test_superuser_create_does_not_adopt_existing_auth_user(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """POST /users/ with an email already registered in GoTrue must 409
    instead of silently linking the pre-existing auth identity."""
    email = random_email()
    supabase_auth.admin_get_or_create_user(email=email, password=random_lower_string())

    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json={"email": email},
    )
    assert r.status_code == 409
    assert "auth provider" in r.json()["message"]

    from app.modules.iam.users import repo as user_repo

    assert user_repo.get_by_email(session=db, email=email) is None


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
