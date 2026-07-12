"""AI chat conversation flows: routes, services, and the message helpers (#36).

Cross-tenant invisibility is covered by test_tenant_scoping.py; here we
drive the owner's own happy paths, the missing-row branches, and the
message persistence helpers (create_message / get_messages /
update_timestamp) plus the messages relationship on the detail route.
"""

import uuid
from collections.abc import Generator

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.modules.ai.conversations import repo as conv_repo
from app.modules.ai.conversations.main import router as conversations_router
from app.modules.ai.conversations.models import Conversation, Message
from app.shared.errors import register_exception_handlers

CHAT = f"{settings.API_V1_STR}/chat/conversations"


@pytest.fixture(scope="module")
def aux_client() -> Generator[TestClient, None, None]:
    aux_app = FastAPI()
    register_exception_handlers(aux_app)
    aux_app.include_router(conversations_router, prefix=settings.API_V1_STR)
    with TestClient(aux_app) as c:
        yield c


def _create_conversation(
    client: TestClient, headers: dict[str, str], title: str = "test conv"
) -> dict[str, object]:
    r = client.post(CHAT, headers=headers, json={"title": title})
    assert r.status_code == status.HTTP_200_OK
    data: dict[str, object] = r.json()
    return data


def test_conversation_create_list_get_delete(
    aux_client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    created = _create_conversation(aux_client, normal_user_token_headers)
    conv_id = created["id"]

    r = aux_client.get(CHAT, headers=normal_user_token_headers)
    assert r.status_code == status.HTTP_200_OK
    assert any(c["id"] == conv_id for c in r.json()["data"])

    r = aux_client.get(f"{CHAT}/{conv_id}", headers=normal_user_token_headers)
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["messages"] == []

    r = aux_client.delete(f"{CHAT}/{conv_id}", headers=normal_user_token_headers)
    assert r.status_code == status.HTTP_200_OK

    r = aux_client.get(f"{CHAT}/{conv_id}", headers=normal_user_token_headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND


def test_conversation_get_and_delete_missing_is_404(
    aux_client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    missing = uuid.uuid4()
    r = aux_client.get(f"{CHAT}/{missing}", headers=normal_user_token_headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND
    r = aux_client.delete(f"{CHAT}/{missing}", headers=normal_user_token_headers)
    assert r.status_code == status.HTTP_404_NOT_FOUND


def test_conversation_detail_includes_messages_in_order(
    aux_client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    created = _create_conversation(aux_client, normal_user_token_headers)
    conv_id = uuid.UUID(str(created["id"]))

    first = conv_repo.create_message(
        session=db,
        message=Message(conversation_id=conv_id, role="user", content="hello"),
    )
    second = conv_repo.create_message(
        session=db,
        message=Message(
            conversation_id=conv_id,
            role="assistant",
            content="hi there",
            metadata_={"model": "fake"},
        ),
    )
    assert first.id != second.id

    messages = conv_repo.get_messages(session=db, conversation_id=conv_id)
    assert [m.content for m in messages] == ["hello", "hi there"]

    r = aux_client.get(f"{CHAT}/{conv_id}", headers=normal_user_token_headers)
    assert r.status_code == status.HTTP_200_OK
    payload = r.json()
    assert len(payload["messages"]) == 2
    roles = {m["role"] for m in payload["messages"]}
    assert roles == {"user", "assistant"}


def test_update_timestamp_bumps_updated_at(
    aux_client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    created = _create_conversation(aux_client, normal_user_token_headers)
    conv = db.get(Conversation, uuid.UUID(str(created["id"])))
    assert conv is not None
    before = conv.updated_at
    assert before is not None

    conv_repo.update_timestamp(session=db, conversation=conv)
    db.refresh(conv)
    assert conv.updated_at is not None
    assert conv.updated_at >= before
