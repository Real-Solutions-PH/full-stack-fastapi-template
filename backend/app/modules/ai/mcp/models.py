import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime
from sqlmodel import Column, Field, SQLModel

from app.core.crypto import EncryptedJSON


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MCPServer(SQLModel, table=True):
    __tablename__ = "mcpserver"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=128)
    url: str = Field(max_length=512)
    # Encrypted at rest: can hold connection secrets (bearer token, auth
    # headers). Write-only at the API; stored as an opaque Fernet blob.
    config: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(EncryptedJSON, nullable=False),
    )
    is_active: bool = True
    created_at: datetime | None = Field(  # type: ignore[call-overload]
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),
    )
