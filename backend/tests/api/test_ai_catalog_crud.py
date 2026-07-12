"""Superuser CRUD flows over the AI catalog (agents / tools / mcp) (#36).

Complements test_ai_catalog_authz.py (which proves the permission wall):
these tests drive the happy paths and error branches of the routes ->
services -> repos stack. Mounted on an auxiliary app because the main app
only includes the AI routers when AI_ENABLED is set.
"""

import uuid
from collections.abc import Generator

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.modules.ai.agents.main import router as agents_router
from app.modules.ai.mcp.main import router as mcp_router
from app.modules.ai.tools.main import router as tools_router
from app.shared.errors import register_exception_handlers
from tests.utils.utils import random_lower_string

AGENTS = f"{settings.API_V1_STR}/agents"
TOOLS = f"{settings.API_V1_STR}/tools"
MCP = f"{settings.API_V1_STR}/mcp"


@pytest.fixture(scope="module")
def aux_client() -> Generator[TestClient, None, None]:
    aux_app = FastAPI()
    register_exception_handlers(aux_app)
    aux_app.include_router(agents_router, prefix=settings.API_V1_STR)
    aux_app.include_router(tools_router, prefix=settings.API_V1_STR)
    aux_app.include_router(mcp_router, prefix=settings.API_V1_STR)
    with TestClient(aux_app) as c:
        yield c


def _create_agent(
    client: TestClient, headers: dict[str, str], name: str | None = None
) -> dict[str, object]:
    r = client.post(
        f"{AGENTS}/",
        headers=headers,
        json={"name": name or f"agent-{random_lower_string()[:12]}"},
    )
    assert r.status_code == status.HTTP_200_OK
    data: dict[str, object] = r.json()
    return data


def _create_tool(
    client: TestClient, headers: dict[str, str], name: str | None = None
) -> dict[str, object]:
    r = client.post(
        f"{TOOLS}/",
        headers=headers,
        json={
            "name": name or f"tool-{random_lower_string()[:12]}",
            "tool_type": "brave_search",
        },
    )
    assert r.status_code == status.HTTP_200_OK
    data: dict[str, object] = r.json()
    return data


# --- agents ---


def test_agent_crud_lifecycle(
    aux_client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    created = _create_agent(aux_client, superuser_token_headers)
    agent_id = created["id"]

    r = aux_client.get(f"{AGENTS}/{agent_id}", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["name"] == created["name"]

    r = aux_client.get(f"{AGENTS}/", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["count"] >= 1
    assert any(a["id"] == agent_id for a in r.json()["data"])

    r = aux_client.put(
        f"{AGENTS}/{agent_id}",
        headers=superuser_token_headers,
        json={"description": "updated", "is_active": False},
    )
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["description"] == "updated"
    assert r.json()["is_active"] is False

    r = aux_client.delete(f"{AGENTS}/{agent_id}", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_200_OK

    r = aux_client.get(f"{AGENTS}/{agent_id}", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND


def test_agent_duplicate_name_is_409(
    aux_client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    created = _create_agent(aux_client, superuser_token_headers)
    r = aux_client.post(
        f"{AGENTS}/",
        headers=superuser_token_headers,
        json={"name": created["name"]},
    )
    assert r.status_code == status.HTTP_409_CONFLICT


def test_agent_update_and_delete_missing_is_404(
    aux_client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    missing = uuid.uuid4()
    r = aux_client.put(
        f"{AGENTS}/{missing}", headers=superuser_token_headers, json={"name": "x"}
    )
    assert r.status_code == status.HTTP_404_NOT_FOUND
    r = aux_client.delete(f"{AGENTS}/{missing}", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND


# --- tools ---


def test_tool_crud_lifecycle(
    aux_client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    created = _create_tool(aux_client, superuser_token_headers)
    tool_id = created["id"]

    r = aux_client.get(f"{TOOLS}/{tool_id}", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_200_OK

    r = aux_client.get(f"{TOOLS}/", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_200_OK
    assert any(t["id"] == tool_id for t in r.json()["data"])

    r = aux_client.put(
        f"{TOOLS}/{tool_id}",
        headers=superuser_token_headers,
        json={"description": "updated"},
    )
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["description"] == "updated"

    r = aux_client.delete(f"{TOOLS}/{tool_id}", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_200_OK
    r = aux_client.get(f"{TOOLS}/{tool_id}", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND


def test_tool_duplicate_name_is_409(
    aux_client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    created = _create_tool(aux_client, superuser_token_headers)
    r = aux_client.post(
        f"{TOOLS}/",
        headers=superuser_token_headers,
        json={"name": created["name"], "tool_type": "brave_search"},
    )
    assert r.status_code == status.HTTP_409_CONFLICT


def test_tool_update_and_delete_missing_is_404(
    aux_client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    missing = uuid.uuid4()
    r = aux_client.put(
        f"{TOOLS}/{missing}", headers=superuser_token_headers, json={"name": "x"}
    )
    assert r.status_code == status.HTTP_404_NOT_FOUND
    r = aux_client.delete(f"{TOOLS}/{missing}", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND


def test_tool_assign_unassign_flow(
    aux_client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    agent = _create_agent(aux_client, superuser_token_headers)
    tool = _create_tool(aux_client, superuser_token_headers)

    r = aux_client.post(
        f"{TOOLS}/agent/{agent['id']}",
        headers=superuser_token_headers,
        json={"tool_id": tool["id"]},
    )
    assert r.status_code == status.HTTP_200_OK

    # duplicate assignment is rejected
    r = aux_client.post(
        f"{TOOLS}/agent/{agent['id']}",
        headers=superuser_token_headers,
        json={"tool_id": tool["id"]},
    )
    assert r.status_code == status.HTTP_409_CONFLICT

    r = aux_client.get(f"{TOOLS}/agent/{agent['id']}", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["count"] == 1
    assert r.json()["data"][0]["id"] == tool["id"]

    r = aux_client.delete(
        f"{TOOLS}/agent/{agent['id']}/{tool['id']}",
        headers=superuser_token_headers,
    )
    assert r.status_code == status.HTTP_200_OK

    r = aux_client.get(f"{TOOLS}/agent/{agent['id']}", headers=superuser_token_headers)
    assert r.json()["count"] == 0

    # unassigning a link that no longer exists is a silent no-op
    r = aux_client.delete(
        f"{TOOLS}/agent/{agent['id']}/{tool['id']}",
        headers=superuser_token_headers,
    )
    assert r.status_code == status.HTTP_200_OK


# --- mcp servers ---


def test_mcp_crud_lifecycle(
    aux_client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    name = f"mcp-{random_lower_string()[:12]}"
    r = aux_client.post(
        f"{MCP}/",
        headers=superuser_token_headers,
        json={"name": name, "url": "http://localhost:1", "config": {}},
    )
    assert r.status_code == status.HTTP_200_OK
    mcp_id = r.json()["id"]

    # duplicate name rejected
    r = aux_client.post(
        f"{MCP}/",
        headers=superuser_token_headers,
        json={"name": name, "url": "http://localhost:2"},
    )
    assert r.status_code == status.HTTP_409_CONFLICT

    r = aux_client.get(f"{MCP}/{mcp_id}", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["name"] == name

    r = aux_client.get(f"{MCP}/", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_200_OK
    assert any(s["id"] == mcp_id for s in r.json()["data"])

    r = aux_client.put(
        f"{MCP}/{mcp_id}",
        headers=superuser_token_headers,
        json={"url": "http://localhost:3", "is_active": False},
    )
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["url"] == "http://localhost:3"
    assert r.json()["is_active"] is False

    r = aux_client.delete(f"{MCP}/{mcp_id}", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_200_OK
    r = aux_client.get(f"{MCP}/{mcp_id}", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND


def test_mcp_update_and_delete_missing_is_404(
    aux_client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    missing = uuid.uuid4()
    r = aux_client.put(
        f"{MCP}/{missing}", headers=superuser_token_headers, json={"name": "x"}
    )
    assert r.status_code == status.HTTP_404_NOT_FOUND
    r = aux_client.delete(f"{MCP}/{missing}", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND
