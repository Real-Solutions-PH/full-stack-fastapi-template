import uuid

from fastapi import HTTPException
from sqlmodel import Session

from app.modules.ai.tools import repo as tool_repo
from app.modules.ai.tools.models import Tool
from app.modules.ai.tools.schema import ToolCreate, ToolUpdate


def list_tools(
    *, session: Session, skip: int = 0, limit: int = 100
) -> tuple[list[Tool], int]:
    return tool_repo.get_multi(session=session, skip=skip, limit=limit)


def get_tool(*, session: Session, tool_id: uuid.UUID) -> Tool:
    tool = tool_repo.get_by_id(session=session, tool_id=tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


def create_tool(*, session: Session, tool_in: ToolCreate) -> Tool:
    existing = tool_repo.get_by_name(session=session, name=tool_in.name)
    if existing:
        raise HTTPException(status_code=409, detail="Tool with this name already exists")
    db_tool = Tool.model_validate(tool_in)
    return tool_repo.create(session=session, tool=db_tool)


def update_tool(
    *, session: Session, tool_id: uuid.UUID, tool_in: ToolUpdate
) -> Tool:
    tool = tool_repo.get_by_id(session=session, tool_id=tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    update_data = tool_in.model_dump(exclude_unset=True)
    return tool_repo.update(session=session, tool=tool, update_data=update_data)


def delete_tool(*, session: Session, tool_id: uuid.UUID) -> None:
    tool = tool_repo.get_by_id(session=session, tool_id=tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    tool_repo.delete(session=session, tool=tool)


def assign_tool_to_agent(
    *, session: Session, agent_id: uuid.UUID, tool_id: uuid.UUID
) -> None:
    existing = tool_repo.get_agent_tool(
        session=session, agent_id=agent_id, tool_id=tool_id
    )
    if existing:
        raise HTTPException(status_code=409, detail="Tool already assigned to agent")
    tool_repo.assign_tool_to_agent(
        session=session, agent_id=agent_id, tool_id=tool_id
    )


def remove_tool_from_agent(
    *, session: Session, agent_id: uuid.UUID, tool_id: uuid.UUID
) -> None:
    tool_repo.remove_tool_from_agent(
        session=session, agent_id=agent_id, tool_id=tool_id
    )


def get_tools_for_agent(
    *, session: Session, agent_id: uuid.UUID
) -> list[Tool]:
    return tool_repo.get_tools_for_agent(session=session, agent_id=agent_id)
