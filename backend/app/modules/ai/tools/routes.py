import uuid
from typing import Any

from fastapi import APIRouter

from app.modules.ai.tools import services as tool_service
from app.modules.ai.tools.schema import (
    AgentToolAssign,
    ToolCreate,
    ToolPublic,
    ToolsPublic,
    ToolUpdate,
)
from app.modules.iam.deps import CurrentUser
from app.shared.deps import SessionDep
from app.shared.schema import Message

router = APIRouter(prefix="/tools", tags=["ai-tools"])


@router.get("/", response_model=ToolsPublic)
def read_tools(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    tools, count = tool_service.list_tools(session=session, skip=skip, limit=limit)
    return ToolsPublic(
        data=[ToolPublic.model_validate(t) for t in tools], count=count
    )


@router.get("/{id}", response_model=ToolPublic)
def read_tool(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    return tool_service.get_tool(session=session, tool_id=id)


@router.post("/", response_model=ToolPublic)
def create_tool(
    *, session: SessionDep, current_user: CurrentUser, tool_in: ToolCreate
) -> Any:
    return tool_service.create_tool(session=session, tool_in=tool_in)


@router.put("/{id}", response_model=ToolPublic)
def update_tool(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    tool_in: ToolUpdate,
) -> Any:
    return tool_service.update_tool(session=session, tool_id=id, tool_in=tool_in)


@router.delete("/{id}")
def delete_tool(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    tool_service.delete_tool(session=session, tool_id=id)
    return Message(message="Tool deleted successfully")


@router.get("/agent/{agent_id}", response_model=ToolsPublic)
def read_agent_tools(
    session: SessionDep, current_user: CurrentUser, agent_id: uuid.UUID
) -> Any:
    tools = tool_service.get_tools_for_agent(session=session, agent_id=agent_id)
    return ToolsPublic(
        data=[ToolPublic.model_validate(t) for t in tools], count=len(tools)
    )


@router.post("/agent/{agent_id}")
def assign_tool(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
    body: AgentToolAssign,
) -> Message:
    tool_service.assign_tool_to_agent(
        session=session, agent_id=agent_id, tool_id=body.tool_id
    )
    return Message(message="Tool assigned to agent")


@router.delete("/agent/{agent_id}/{tool_id}")
def unassign_tool(
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
    tool_id: uuid.UUID,
) -> Message:
    tool_service.remove_tool_from_agent(
        session=session, agent_id=agent_id, tool_id=tool_id
    )
    return Message(message="Tool removed from agent")
