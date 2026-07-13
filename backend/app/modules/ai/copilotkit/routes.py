"""AG-UI routes: the agent catalog plus one run route per agent."""

import logging
from collections.abc import AsyncIterator, Awaitable, Callable

from ag_ui.core import EventType, RunAgentInput, RunErrorEvent
from ag_ui.encoder import EventEncoder
from copilotkit import LangGraphAGUIAgent
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.memory import InMemorySaver

from app.modules.ai.agents.definitions.fast import build_fast_agent
from app.modules.ai.agents.definitions.plan_and_execute import (
    build_plan_and_execute_agent,
)
from app.modules.ai.agents.definitions.react import build_react_agent

from .paths import COPILOTKIT_PATH

logger = logging.getLogger(__name__)


def build_agents() -> list[LangGraphAGUIAgent]:
    """Build the chat agent catalog exposed over AG-UI.

    Graphs get an in-process ``InMemorySaver`` checkpointer: the AG-UI
    LangGraph adapter requires one (``aget_state`` on every run). Thread
    state therefore lives in RAM per backend process — acceptable for the
    template; swap in ``langgraph-checkpoint-postgres`` for durable threads.
    """
    return [
        LangGraphAGUIAgent(
            name="fast",
            description="Simple direct LLM - fastest response, no tools",
            graph=build_fast_agent().compile(checkpointer=InMemorySaver()),
        ),
        LangGraphAGUIAgent(
            name="react",
            description="ReAct agent with tool calling",
            graph=build_react_agent(
                tool_names=["brave_search"], checkpointer=InMemorySaver()
            ),
        ),
        LangGraphAGUIAgent(
            name="plan_and_execute",
            description="Plans then executes step by step",
            graph=build_plan_and_execute_agent(tool_names=["brave_search"]).compile(
                checkpointer=InMemorySaver()
            ),
        ),
    ]


def _make_run_handler(
    agent: LangGraphAGUIAgent,
) -> Callable[[RunAgentInput, Request], Awaitable[StreamingResponse]]:
    async def run_agent(
        input_data: RunAgentInput, request: Request
    ) -> StreamingResponse:
        encoder = EventEncoder(accept=request.headers.get("accept", ""))
        # Clone per request: LangGraphAgent keeps per-run state on the
        # instance; sharing one across concurrent requests corrupts it.
        request_agent = agent.clone()

        async def event_stream() -> AsyncIterator[str]:
            # The upstream adapter propagates run exceptions (LLM auth
            # failure, tool crash) instead of emitting a terminal event —
            # emit RUN_ERROR ourselves so clients see an error, not a
            # truncated stream.
            try:
                async for event in request_agent.run(input_data):
                    yield encoder.encode(event)
            except Exception as exc:  # noqa: BLE001 - terminal stream event
                logger.exception("AG-UI run failed", exc_info=exc)
                yield encoder.encode(
                    RunErrorEvent(type=EventType.RUN_ERROR, message="Agent run failed")
                )

        return StreamingResponse(
            event_stream(),
            media_type=encoder.get_content_type(),
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return run_agent


def build_agui_router(agents: list[LangGraphAGUIAgent]) -> APIRouter:
    """AG-UI routes: one info route plus a run route per agent.

    ``include_in_schema=False`` — the AG-UI protocol is not part of the REST
    surface, so it must not leak into OpenAPI / the generated clients.
    """
    # tags: main.py's generate_unique_id derives route ids from tags[0];
    # untagged routes crash app startup even when excluded from the schema.
    router = APIRouter(include_in_schema=False, tags=["copilotkit"])
    catalog = [{"name": a.name, "description": a.description} for a in agents]

    @router.get(COPILOTKIT_PATH)
    async def copilotkit_info() -> dict[str, object]:
        return {"protocol": "ag-ui", "agents": catalog}

    for agent in agents:
        router.add_api_route(
            f"{COPILOTKIT_PATH}/agents/{agent.name}",
            _make_run_handler(agent),
            methods=["POST"],
            name=f"copilotkit_run_{agent.name}",
        )
    return router
