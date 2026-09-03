"""The global request-body-size guard rejects oversize payloads with 413."""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import BodySizeLimitMiddleware


@pytest.fixture
def limited_client() -> TestClient:
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware)

    @app.post("/echo")
    async def echo(request: Request) -> dict[str, int]:
        body = await request.body()
        return {"len": len(body)}

    return TestClient(app)


def test_body_within_limit_is_accepted(
    limited_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "MAX_REQUEST_BODY_SIZE_MB", 1)
    r = limited_client.post("/echo", content=b"x" * 100)
    assert r.status_code == 200
    assert r.json()["len"] == 100


def test_body_over_declared_content_length_is_rejected(
    limited_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "MAX_REQUEST_BODY_SIZE_MB", 1)
    r = limited_client.post("/echo", content=b"x" * (2 * 1024 * 1024))
    assert r.status_code == 413
    assert r.json()["code"] == "payload_too_large"
