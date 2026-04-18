import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime
from sqlmodel import Column, Field, Relationship, SQLModel

from app.modules.iam.tenants.models import Tenant
from app.modules.iam.users.models import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MCPServer(SQLModel, table=True):
    __tablename__ = "chat_mcp_server"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=128)
    description: str | None = Field(default=None, max_length=512)
    transport: str = Field(max_length=32, default="stdio")
    command: str | None = Field(default=None, max_length=512)
    args: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    url: str | None = Field(default=None, max_length=512)
    env: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))
    enabled: bool = True
    created_at: datetime | None = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class Tool(SQLModel, table=True):
    __tablename__ = "chat_tool"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=128)
    description: str | None = Field(default=None, max_length=512)
    kind: str = Field(max_length=32, default="builtin")
    builtin_key: str | None = Field(default=None, max_length=128)
    mcp_server_id: uuid.UUID | None = Field(
        default=None, foreign_key="chat_mcp_server.id", ondelete="SET NULL"
    )
    config: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    enabled: bool = True
    created_at: datetime | None = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class Agent(SQLModel, table=True):
    __tablename__ = "chat_agent"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=128)
    slug: str = Field(unique=True, index=True, max_length=64)
    description: str | None = Field(default=None, max_length=512)
    workflow: str = Field(max_length=32, default="react")
    system_prompt: str = Field(default="You are a helpful assistant.")
    model: str = Field(max_length=128, default="gpt-4o-mini")
    provider: str | None = Field(default=None, max_length=32)
    temperature: float = 0.2
    tool_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    is_default: bool = False
    enabled: bool = True
    created_at: datetime | None = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    sessions: list["ChatSession"] = Relationship(
        back_populates="agent", cascade_delete=True
    )


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_session"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str | None = Field(default=None, max_length=255)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    tenant_id: uuid.UUID = Field(
        foreign_key="tenant.id", nullable=False, ondelete="CASCADE"
    )
    agent_id: uuid.UUID = Field(
        foreign_key="chat_agent.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime | None = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime | None = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    agent: Agent | None = Relationship(back_populates="sessions")
    messages: list["Message"] = Relationship(
        back_populates="session", cascade_delete=True
    )


class Message(SQLModel, table=True):
    __tablename__ = "chat_message"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(
        foreign_key="chat_session.id", nullable=False, ondelete="CASCADE", index=True
    )
    role: str = Field(max_length=32)
    content: str = Field(default="")
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    meta: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime | None = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    session: ChatSession | None = Relationship(back_populates="messages")


__all__ = [
    "Agent",
    "ChatSession",
    "MCPServer",
    "Message",
    "Tool",
    "Tenant",
    "User",
]
