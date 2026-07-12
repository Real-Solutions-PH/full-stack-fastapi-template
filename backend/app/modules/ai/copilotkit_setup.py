"""AG-UI chat transport (constitution §5.2, ADR-0007).

The three LangGraph agents are exposed as AG-UI endpoints served straight
from this FastAPI app — LangGraph runs in-process, events stream to the
browser as SSE, and there is no webhook hop or sidecar runtime service.

Routes (all guarded by the bearer-token middleware below):

- ``GET  {COPILOTKIT_PATH}``                    — info: lists the agents.
- ``POST {COPILOTKIT_PATH}/agents/{name}``      — run: AG-UI ``RunAgentInput``
  in, SSE event stream out.

The frontend talks to the run routes directly with ``@ag-ui/client``'s
``HttpAgent`` (CopilotKit v2 ``selfManagedAgents``) — there is no CopilotKit
GraphQL runtime anywhere. ``copilotkit.CopilotKitRemoteEndpoint`` /
``add_fastapi_endpoint`` are deliberately NOT used: their agent routes call
``agent.execute()``, which ``LangGraphAGUIAgent`` (an AG-UI agent with
``run()``) does not implement — that protocol is dead code for this path.
"""

import logging
from collections.abc import AsyncIterator, Awaitable, Callable

import jwt
from ag_ui.core import EventType, RunAgentInput, RunErrorEvent
from ag_ui.encoder import EventEncoder
from copilotkit import LangGraphAGUIAgent
from fastapi import APIRouter, FastAPI, Request, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from langgraph.checkpoint.memory import InMemorySaver

from app.core import supabase_auth
from app.core.config import settings
from app.modules.ai.agents.definitions.fast import build_fast_agent
from app.modules.ai.agents.definitions.plan_and_execute import (
    build_plan_and_execute_agent,
)
from app.modules.ai.agents.definitions.react import build_react_agent

logger = logging.getLogger(__name__)

COPILOTKIT_PATH = f"{settings.API_V1_STR}/copilotkit"


def _envelope(
    status_code: int, code: str, message: str, request: Request
) -> JSONResponse:
    headers: dict[str, str] = {"Vary": "Origin"}
    if status_code == 401:
        headers["WWW-Authenticate"] = "Bearer"
    # This middleware sits OUTSIDE CORSMiddleware, so error responses must
    # echo CORS themselves or the browser can't read them (same pattern as
    # the 500 handler in app/shared/errors.py).
    origin = request.headers.get("origin")
    if origin and origin in settings.all_cors_origins:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message, "details": None},
        headers=headers,
    )


def _auth_failure_response(request: Request) -> JSONResponse | None:
    """Return an error envelope if the bearer token doesn't authenticate.

    None means the token verified. A JWKS connection failure is surfaced
    as 503 (upstream outage), not 401 — same distinction as
    ``get_current_user``.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return _envelope(
            status.HTTP_401_UNAUTHORIZED, "unauthorized", "Not authenticated", request
        )
    try:
        supabase_auth.verify_token(auth.removeprefix("Bearer "))
    except jwt.exceptions.PyJWKClientConnectionError:
        return _envelope(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "auth_unavailable",
            "Authentication service unavailable",
            request,
        )
    except jwt.PyJWTError:
        return _envelope(
            status.HTTP_401_UNAUTHORIZED, "unauthorized", "Not authenticated", request
        )
    return None


def install_copilotkit_auth(app: FastAPI) -> None:
    """Require a valid bearer token on every route under the chat mount.

    The AG-UI routes are registered without per-route ``CurrentUser``
    dependencies — without this middleware the chat transport is anonymous
    LLM/tool invocation (cost abuse). Signature-only check (no DB lookup).
    """

    @app.middleware("http")
    async def copilotkit_auth(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # CORS preflights carry no Authorization header and must reach
        # CORSMiddleware (which sits INSIDE this middleware) untouched.
        if request.method != "OPTIONS" and request.url.path.startswith(COPILOTKIT_PATH):
            failure = _auth_failure_response(request)
            if failure is not None:
                return failure
        return await call_next(request)


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


def setup_copilotkit(app: FastAPI) -> None:
    """Mount the AG-UI chat transport with bearer-token auth."""
    install_copilotkit_auth(app)
    app.include_router(build_agui_router(build_agents()))
