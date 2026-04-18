import uuid
from typing import Any

from fastapi import APIRouter

from app.modules.ai.mcp import services as mcp_service
from app.modules.ai.mcp.schema import (
    MCPServerCreate,
    MCPServerPublic,
    MCPServersPublic,
    MCPServerUpdate,
)
from app.modules.iam.deps import CurrentUser
from app.shared.deps import SessionDep
from app.shared.schema import Message

router = APIRouter(prefix="/mcp", tags=["ai-mcp"])


@router.get("/", response_model=MCPServersPublic)
def read_mcp_servers(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    servers, count = mcp_service.list_mcp_servers(
        session=session, skip=skip, limit=limit
    )
    return MCPServersPublic(
        data=[MCPServerPublic.model_validate(s) for s in servers], count=count
    )


@router.get("/{id}", response_model=MCPServerPublic)
def read_mcp_server(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    return mcp_service.get_mcp_server(session=session, mcp_id=id)


@router.post("/", response_model=MCPServerPublic)
def create_mcp_server(
    *, session: SessionDep, current_user: CurrentUser, mcp_in: MCPServerCreate
) -> Any:
    return mcp_service.create_mcp_server(session=session, mcp_in=mcp_in)


@router.put("/{id}", response_model=MCPServerPublic)
def update_mcp_server(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    mcp_in: MCPServerUpdate,
) -> Any:
    return mcp_service.update_mcp_server(session=session, mcp_id=id, mcp_in=mcp_in)


@router.delete("/{id}")
def delete_mcp_server(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    mcp_service.delete_mcp_server(session=session, mcp_id=id)
    return Message(message="MCP server deleted successfully")
