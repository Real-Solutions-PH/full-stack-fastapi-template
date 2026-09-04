"""The per-request tenant session enforces RLS through the app engine.

Proves the claim payload built by ``deps._tenant_claims_json`` and installed
by ``deps.install_tenant_claims`` is the shape ``app_tenant_id()`` reads, so a
session on the non-owner ``app_user`` role only sees its own tenant's rows —
and stays isolated across a commit (claims are re-applied per transaction).
"""

import secrets
import uuid
from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlmodel import Session

from app.core import rls
from app.core.config import settings
from app.core.db import engine as owner_engine
from app.db.models import Item, Tenant, User
from app.modules.iam import deps
from tests.utils.utils import random_email, random_lower_string

APP_USER_PASSWORD = secrets.token_urlsafe(24)


@pytest.fixture(scope="module")
def rows() -> Generator[dict[str, Any], None, None]:
    made: dict[str, Any] = {}
    with Session(owner_engine) as db:
        for label in ("a", "b"):
            tenant = Tenant(
                name=f"ts tenant {label}",
                slug=f"ts-{label}-{random_lower_string()[:8]}",
            )
            db.add(tenant)
            db.commit()
            user = User(email=random_email(), tenant_id=tenant.id)
            db.add(user)
            db.commit()
            item = Item(title=f"ts item {label}", owner_id=user.id, tenant_id=tenant.id)
            db.add(item)
            db.commit()
            made[label] = {
                "tenant_id": tenant.id,
                "user_id": user.id,
                "item_id": item.id,
            }
        yield made
        for label in ("a", "b"):
            ids = made[label]
            db.execute(text("DELETE FROM item WHERE id = :id"), {"id": ids["item_id"]})
            db.execute(
                text('DELETE FROM "user" WHERE id = :id'), {"id": ids["user_id"]}
            )
            db.execute(
                text("DELETE FROM tenant WHERE id = :id"), {"id": ids["tenant_id"]}
            )
        db.commit()


@pytest.fixture(scope="module")
def app_user_engine(rows: dict[str, Any]) -> Generator[Engine, None, None]:  # noqa: ARG001
    with owner_engine.connect() as conn:
        conn.execute(text(f"ALTER ROLE app_user LOGIN PASSWORD '{APP_USER_PASSWORD}'"))
        conn.commit()
    url = (
        f"postgresql+psycopg://app_user:{APP_USER_PASSWORD}"
        f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    eng = create_engine(url, pool_size=1, max_overflow=0)
    try:
        yield eng
    finally:
        eng.dispose()
        with owner_engine.connect() as conn:
            conn.execute(text("ALTER ROLE app_user NOLOGIN PASSWORD NULL"))
            conn.commit()


def _user_for(tenant_id: uuid.UUID) -> User:
    return User(id=uuid.uuid4(), email=random_email(), tenant_id=tenant_id)


def test_tenant_claims_json_carries_tenant_id() -> None:
    import json

    tid = uuid.uuid4()
    claims = json.loads(deps._tenant_claims_json(_user_for(tid)))
    assert claims["tenant_id"] == str(tid)
    assert claims["role"] == "authenticated"


def test_tenant_session_sees_only_its_tenant(
    app_user_engine: Engine, rows: dict[str, Any]
) -> None:
    a, b = rows["a"], rows["b"]
    claims = deps._tenant_claims_json(_user_for(a["tenant_id"]))
    with Session(app_user_engine) as session:
        deps.install_tenant_claims(session, claims)
        item_ids = {r[0] for r in session.execute(text("SELECT id FROM item"))}
    assert a["item_id"] in item_ids
    assert b["item_id"] not in item_ids


def test_tenant_session_stays_isolated_after_commit(
    app_user_engine: Engine, rows: dict[str, Any]
) -> None:
    # After a commit the txn-local GUC resets to ''; the after_begin hook must
    # re-apply the claim so the next transaction is still scoped.
    a, b = rows["a"], rows["b"]
    claims = deps._tenant_claims_json(_user_for(a["tenant_id"]))
    with Session(app_user_engine) as session:
        deps.install_tenant_claims(session, claims)
        first = {r[0] for r in session.execute(text("SELECT id FROM item"))}
        session.commit()
        second = {r[0] for r in session.execute(text("SELECT id FROM item"))}
    assert a["item_id"] in first
    assert a["item_id"] in second
    assert b["item_id"] not in second


# --- startup posture check --------------------------------------------------


def test_owner_engine_is_reported_as_bypassing() -> None:
    bypasses, _role = rls._connection_bypasses_rls(owner_engine)
    assert bypasses is True


def test_posture_warns_in_local_without_raising() -> None:
    assert settings.ENVIRONMENT == "local"
    rls.check_rls_posture()  # owner engine bypasses, but local -> warn, no raise


def test_posture_raises_when_app_user_set_but_bypassing_outside_local(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "POSTGRES_APP_USER", "app_user")
    monkeypatch.setattr(
        rls, "_connection_bypasses_rls", lambda _engine: (True, "postgres")
    )
    with pytest.raises(RuntimeError, match="RLS misconfigured"):
        rls.check_rls_posture()
