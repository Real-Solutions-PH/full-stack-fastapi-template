import uuid
from datetime import datetime
from typing import Any

from sqlmodel import SQLModel


class MCPServerBase(SQLModel):
    name: str
    url: str
    config: dict[str, Any] = {}
    is_active: bool = True


class MCPServerCreate(MCPServerBase):
    pass


class MCPServerUpdate(SQLModel):
    name: str | None = None
    url: str | None = None
    config: dict[str, Any] | None = None
    is_active: bool | None = None


class MCPServerPublic(MCPServerBase):
    id: uuid.UUID
    created_at: datetime | None = None


class MCPServersPublic(SQLModel):
    data: list[MCPServerPublic]
    count: int
