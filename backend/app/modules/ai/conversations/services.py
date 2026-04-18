import uuid

from fastapi import HTTPException
from sqlmodel import Session

from app.modules.ai.conversations import repo as conv_repo
from app.modules.ai.conversations.models import Conversation
from app.modules.ai.conversations.schema import ConversationCreate


def list_conversations(
    *, session: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 50
) -> tuple[list[Conversation], int]:
    return conv_repo.get_multi_by_user(
        session=session, user_id=user_id, skip=skip, limit=limit
    )


def get_conversation_with_messages(
    *, session: Session, user_id: uuid.UUID, conversation_id: uuid.UUID
) -> Conversation:
    conversation = conv_repo.get_by_id(
        session=session, conversation_id=conversation_id
    )
    if not conversation or conversation.user_id != user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def create_conversation(
    *, session: Session, user_id: uuid.UUID, conv_in: ConversationCreate
) -> Conversation:
    db_conv = Conversation(
        user_id=user_id,
        title=conv_in.title,
        agent_id=conv_in.agent_id,
    )
    return conv_repo.create(session=session, conversation=db_conv)


def delete_conversation(
    *, session: Session, user_id: uuid.UUID, conversation_id: uuid.UUID
) -> None:
    conversation = conv_repo.get_by_id(
        session=session, conversation_id=conversation_id
    )
    if not conversation or conversation.user_id != user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv_repo.delete(session=session, conversation=conversation)
