import uuid
from datetime import datetime
from typing import Any

from sqlmodel import SQLModel


class ToolBase(SQLModel):
    name: str
    description: str | None = None
    tool_type: str
    config: dict[str, Any] = {}
    is_active: bool = True


class ToolCreate(ToolBase):
    pass


class ToolUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    config: dict[str, Any] | None = None
    is_active: bool | None = None


class ToolPublic(ToolBase):
    id: uuid.UUID
    created_at: datetime | None = None


class ToolsPublic(SQLModel):
    data: list[ToolPublic]
    count: int


class AgentToolAssign(SQLModel):
    tool_id: uuid.UUID
