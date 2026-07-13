import uuid
from typing import Any

from fastapi import APIRouter

from app.modules.ai.conversations import services as conv_service
from app.modules.ai.conversations.schema import (
    ConversationCreate,
    ConversationPublic,
    ConversationsPublic,
    ConversationWithMessages,
)
from app.modules.iam.deps import CurrentUser
from app.shared.deps import SessionDep
from app.shared.rate_limit import rate_limited
from app.shared.schema import Message

router = APIRouter(prefix="/chat", tags=["ai-chat"])


@router.get("/conversations", response_model=ConversationsPublic)
def read_conversations(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    conversations, count = conv_service.list_conversations(
        session=session, current_user=current_user, skip=skip, limit=limit
    )
    return ConversationsPublic(
        data=[ConversationPublic.model_validate(c) for c in conversations],
        count=count,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
def read_conversation(
    session: SessionDep,
    current_user: CurrentUser,
    conversation_id: uuid.UUID,
) -> Any:
    return conv_service.get_conversation_with_messages(
        session=session,
        current_user=current_user,
        conversation_id=conversation_id,
    )


@router.post(
    "/conversations",
    response_model=ConversationPublic,
    dependencies=[rate_limited("ai-chat")],
)
def create_conversation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    conv_in: ConversationCreate,
) -> Any:
    return conv_service.create_conversation(
        session=session, current_user=current_user, conv_in=conv_in
    )


@router.delete(
    "/conversations/{conversation_id}", dependencies=[rate_limited("ai-chat")]
)
def delete_conversation(
    session: SessionDep,
    current_user: CurrentUser,
    conversation_id: uuid.UUID,
) -> Message:
    conv_service.delete_conversation(
        session=session,
        current_user=current_user,
        conversation_id=conversation_id,
    )
    return Message(message="Conversation deleted successfully")
