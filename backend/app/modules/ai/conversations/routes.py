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
        session=session, user_id=current_user.id, skip=skip, limit=limit
    )
    return ConversationsPublic(
        data=[ConversationPublic.model_validate(c) for c in conversations],
        count=count,
    )


@router.get(
    "/conversations/{conversation_id}", response_model=ConversationWithMessages
)
def read_conversation(
    session: SessionDep,
    current_user: CurrentUser,
    conversation_id: uuid.UUID,
) -> Any:
    return conv_service.get_conversation_with_messages(
        session=session,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )


@router.post("/conversations", response_model=ConversationPublic)
def create_conversation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    conv_in: ConversationCreate,
) -> Any:
    return conv_service.create_conversation(
        session=session, user_id=current_user.id, conv_in=conv_in
    )


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    session: SessionDep,
    current_user: CurrentUser,
    conversation_id: uuid.UUID,
) -> Message:
    conv_service.delete_conversation(
        session=session,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    return Message(message="Conversation deleted successfully")
