"""The audit trail must record WHO performed a privileged mutation.

These are HTTP-level: they drive the routes with a real superuser token and
assert the persisted audit row's ``actor_id`` is the acting superuser. A
service-layer test cannot catch the gap they guard — the acting user is only
known at the route, and the bug was the route never forwarding it.

AI catalog routes (tools / mcp / agents) are mounted on an auxiliary app: the
main app only includes them when AI_ENABLED is set.
"""

import uuid
from collections.abc import Generator

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlmodel import Session, col, select

from app.core.config import settings
from app.db.models import AuditLog
from app.modules.ai.agents.main import router as agents_router
from app.modules.ai.mcp.main import router as mcp_router
from app.modules.ai.tools.main import router as tools_router
from app.modules.iam.users import repo as user_repo
from app.shared.errors import register_exception_handlers
from tests.utils.user import create_random_user
from tests.utils.utils import random_email, random_lower_string

TOOLS = f"{settings.API_V1_STR}/tools"
MCP = f"{settings.API_V1_STR}/mcp"
AGENTS = f"{settings.API_V1_STR}/agents"
USERS = f"{settings.API_V1_STR}/users"


@pytest.fixture(scope="module")
def aux_client() -> Generator[TestClient, None, None]:
    aux_app = FastAPI()
    register_exception_handlers(aux_app)
    aux_app.include_router(agents_router, prefix=settings.API_V1_STR)
    aux_app.include_router(tools_router, prefix=settings.API_V1_STR)
    aux_app.include_router(mcp_router, prefix=settings.API_V1_STR)
    with TestClient(aux_app) as c:
        yield c


def _superuser_id(db: Session) -> uuid.UUID:
    user = user_repo.get_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    return user.id


def _last_actor(db: Session, action: str, target_id: object) -> uuid.UUID | None:
    row = db.exec(
        select(AuditLog)
        .where(AuditLog.action == action, AuditLog.target_id == str(target_id))
        .order_by(col(AuditLog.created_at).desc())
    ).first()
    assert row is not None, f"no audit row for {action}/{target_id}"
    return row.actor_id


def test_user_create_records_acting_superuser(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    r = client.post(
        f"{USERS}/", headers=superuser_token_headers, json={"email": random_email()}
    )
    assert r.status_code == status.HTTP_200_OK
    assert _last_actor(db, "user.create", r.json()["id"]) == _superuser_id(db)


def test_user_update_records_acting_superuser(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    target = create_random_user(db)
    r = client.patch(
        f"{USERS}/{target.id}",
        headers=superuser_token_headers,
        json={"full_name": "Audited"},
    )
    assert r.status_code == status.HTTP_200_OK
    assert _last_actor(db, "user.update", target.id) == _superuser_id(db)


def test_mcp_crud_records_acting_superuser(
    aux_client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    su = _superuser_id(db)
    r = aux_client.post(
        f"{MCP}/",
        headers=superuser_token_headers,
        json={"name": f"srv-{random_lower_string()[:10]}", "url": "https://ex.com/sse"},
    )
    assert r.status_code == status.HTTP_200_OK
    mcp_id = r.json()["id"]
    assert _last_actor(db, "mcp_server.create", mcp_id) == su

    r = aux_client.put(
        f"{MCP}/{mcp_id}", headers=superuser_token_headers, json={"is_active": False}
    )
    assert r.status_code == status.HTTP_200_OK
    assert _last_actor(db, "mcp_server.update", mcp_id) == su

    r = aux_client.delete(f"{MCP}/{mcp_id}", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_200_OK
    assert _last_actor(db, "mcp_server.delete", mcp_id) == su


def test_tool_crud_records_acting_superuser(
    aux_client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    su = _superuser_id(db)
    r = aux_client.post(
        f"{TOOLS}/",
        headers=superuser_token_headers,
        json={
            "name": f"tool-{random_lower_string()[:10]}",
            "tool_type": "brave_search",
        },
    )
    assert r.status_code == status.HTTP_200_OK
    tool_id = r.json()["id"]
    assert _last_actor(db, "tool.create", tool_id) == su

    r = aux_client.put(
        f"{TOOLS}/{tool_id}",
        headers=superuser_token_headers,
        json={"description": "updated"},
    )
    assert r.status_code == status.HTTP_200_OK
    assert _last_actor(db, "tool.update", tool_id) == su

    r = aux_client.delete(f"{TOOLS}/{tool_id}", headers=superuser_token_headers)
    assert r.status_code == status.HTTP_200_OK
    assert _last_actor(db, "tool.delete", tool_id) == su


def test_tool_assignment_records_acting_superuser(
    aux_client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    su = _superuser_id(db)
    agent = aux_client.post(
        f"{AGENTS}/",
        headers=superuser_token_headers,
        json={"name": f"agent-{random_lower_string()[:10]}"},
    ).json()
    tool = aux_client.post(
        f"{TOOLS}/",
        headers=superuser_token_headers,
        json={
            "name": f"tool-{random_lower_string()[:10]}",
            "tool_type": "brave_search",
        },
    ).json()

    r = aux_client.post(
        f"{TOOLS}/agent/{agent['id']}",
        headers=superuser_token_headers,
        json={"tool_id": tool["id"]},
    )
    assert r.status_code == status.HTTP_200_OK
    assert _last_actor(db, "tool.assign_to_agent", tool["id"]) == su

    r = aux_client.delete(
        f"{TOOLS}/agent/{agent['id']}/{tool['id']}", headers=superuser_token_headers
    )
    assert r.status_code == status.HTTP_200_OK
    assert _last_actor(db, "tool.remove_from_agent", tool["id"]) == su
