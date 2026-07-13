"""Unit tests for the per-tenant rate-limit seam."""

import uuid

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.shared import rate_limit
from app.shared.errors import register_exception_handlers
from app.shared.rate_limit import NullBackend, check_rate_limit
from app.shared.tenancy import TenantContext


class DenyBackend:
    """Backend that denies everything and records what it was asked."""

    def __init__(self) -> None:
        self.calls: list[tuple[uuid.UUID, str, int]] = []

    def allow(self, tenant_id: uuid.UUID, key: str, cost: int) -> bool:
        self.calls.append((tenant_id, key, cost))
        return False


def _ctx() -> TenantContext:
    return TenantContext(tenant_id=uuid.uuid4(), user_id=uuid.uuid4())


def test_null_backend_always_allows() -> None:
    backend = NullBackend()
    assert backend.allow(uuid.uuid4(), "api", 1) is True


def test_check_rate_limit_is_a_noop_with_null_backend() -> None:
    check_rate_limit(_ctx())  # must not raise


def test_check_rate_limit_raises_429_when_backend_denies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deny = DenyBackend()
    monkeypatch.setattr(rate_limit, "backend", deny)
    ctx = _ctx()

    with pytest.raises(HTTPException) as exc_info:
        check_rate_limit(ctx, "items", cost=3)

    assert exc_info.value.status_code == 429
    assert deny.calls == [(ctx.tenant_id, "items", 3)]


def test_429_uses_the_error_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rate_limit, "backend", DenyBackend())

    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/limited")
    def limited() -> dict[str, bool]:
        check_rate_limit(_ctx())
        return {"ok": True}

    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/limited")

    assert r.status_code == 429
    body = r.json()
    assert set(body) == {"code", "message", "details"}
    assert body["code"] == "too_many_requests"
