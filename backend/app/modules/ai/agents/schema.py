import uuid
from datetime import datetime
from typing import Any

from sqlmodel import SQLModel


class AgentBase(SQLModel):
    name: str
    description: str | None = None
    config: dict[str, Any] = {}
    is_active: bool = True


class AgentCreate(AgentBase):
    pass


class AgentUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    config: dict[str, Any] | None = None
    is_active: bool | None = None


class AgentPublic(AgentBase):
    id: uuid.UUID
    created_at: datetime | None = None


class AgentsPublic(SQLModel):
    data: list[AgentPublic]
    count: int
