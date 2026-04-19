import uuid

from fastapi import HTTPException
from sqlmodel import Session

from app.modules.ai.mcp import repo as mcp_repo
from app.modules.ai.mcp.models import MCPServer
from app.modules.ai.mcp.schema import MCPServerCreate, MCPServerUpdate


def list_mcp_servers(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[MCPServer], int]:
    return mcp_repo.get_multi(session=session, skip=skip, limit=limit)


def get_mcp_server(*, session: Session, mcp_id: uuid.UUID) -> MCPServer:
    server = mcp_repo.get_by_id(session=session, mcp_id=mcp_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return server


def create_mcp_server(*, session: Session, mcp_in: MCPServerCreate) -> MCPServer:
    existing = mcp_repo.get_by_name(session=session, name=mcp_in.name)
    if existing:
        raise HTTPException(
            status_code=409, detail="MCP server with this name already exists"
        )
    db_server = MCPServer.model_validate(mcp_in)
    return mcp_repo.create(session=session, mcp_server=db_server)


def update_mcp_server(
    *, session: Session, mcp_id: uuid.UUID, mcp_in: MCPServerUpdate
) -> MCPServer:
    server = mcp_repo.get_by_id(session=session, mcp_id=mcp_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    update_data = mcp_in.model_dump(exclude_unset=True)
    return mcp_repo.update(session=session, mcp_server=server, update_data=update_data)


def delete_mcp_server(*, session: Session, mcp_id: uuid.UUID) -> None:
    server = mcp_repo.get_by_id(session=session, mcp_id=mcp_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    mcp_repo.delete(session=session, mcp_server=server)
