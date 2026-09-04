"""Connection-secret config for MCP servers and tools is encrypted at rest.

Complements test_ai_catalog_crud.py::test_mcp_config_not_echoed (which proves
config never leaves over the API). Here we go under the API to the raw column
and prove a DB dump alone never exposes the secret: the stored bytes are
ciphertext, and only decryption recovers the original.
"""

from collections.abc import Generator

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session

from app.core import crypto
from app.core.config import settings
from app.core.db import engine
from app.modules.ai.mcp.main import router as mcp_router
from app.modules.ai.tools.main import router as tools_router
from app.shared.errors import register_exception_handlers
from tests.utils.utils import random_lower_string

MCP = f"{settings.API_V1_STR}/mcp"
TOOLS = f"{settings.API_V1_STR}/tools"
_SECRET = "S3CR3T-at-rest"


@pytest.fixture(scope="module")
def aux_client() -> Generator[TestClient, None, None]:
    aux_app = FastAPI()
    register_exception_handlers(aux_app)
    aux_app.include_router(tools_router, prefix=settings.API_V1_STR)
    aux_app.include_router(mcp_router, prefix=settings.API_V1_STR)
    with TestClient(aux_app) as c:
        yield c


def _raw_config(table: str, row_id: str) -> bytes:
    """The config column exactly as stored, bypassing the ORM's decryption."""
    with Session(engine) as session:
        raw = session.execute(
            text(f"SELECT config FROM {table} WHERE id = :id"),  # noqa: S608
            {"id": row_id},
        ).scalar_one()
    return bytes(raw)


def test_mcp_config_stored_encrypted(
    aux_client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = aux_client.post(
        f"{MCP}/",
        headers=superuser_token_headers,
        json={
            "name": f"mcp-{random_lower_string()[:12]}",
            "url": "https://mcp.example.com/sse",
            "config": {"auth_token": _SECRET},
        },
    )
    assert r.status_code == status.HTTP_200_OK
    stored = _raw_config("mcpserver", r.json()["id"])

    assert _SECRET.encode() not in stored  # not plaintext at rest
    assert b"auth_token" not in stored  # not even the key name
    assert crypto.decrypt_json(stored) == {"auth_token": _SECRET}  # recoverable


def test_tool_config_stored_encrypted(
    aux_client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = aux_client.post(
        f"{TOOLS}/",
        headers=superuser_token_headers,
        json={
            "name": f"tool-{random_lower_string()[:12]}",
            "tool_type": "brave_search",
            "config": {"api_key": _SECRET},
        },
    )
    assert r.status_code == status.HTTP_200_OK
    stored = _raw_config("tool", r.json()["id"])

    assert _SECRET.encode() not in stored
    assert crypto.decrypt_json(stored) == {"api_key": _SECRET}


def test_empty_config_defaults_round_trip(
    aux_client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # A row created without a config still stores a valid (encrypted) {} — the
    # column is NOT NULL and the default flows through the encrypting type.
    r = aux_client.post(
        f"{MCP}/",
        headers=superuser_token_headers,
        json={
            "name": f"mcp-{random_lower_string()[:12]}",
            "url": "https://mcp.example.com/sse",
        },
    )
    assert r.status_code == status.HTTP_200_OK
    assert crypto.decrypt_json(_raw_config("mcpserver", r.json()["id"])) == {}
