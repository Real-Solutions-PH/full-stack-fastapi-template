from collections.abc import Awaitable, Callable

import jwt
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAGUIAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse

from app.core import supabase_auth
from app.core.config import settings
from app.modules.ai.agents.definitions.fast import build_fast_agent
from app.modules.ai.agents.definitions.plan_and_execute import (
    build_plan_and_execute_agent,
)
from app.modules.ai.agents.definitions.react import build_react_agent

COPILOTKIT_PATH = f"{settings.API_V1_STR}/copilotkit"


def _bearer_token_is_valid(request: Request) -> bool:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    try:
        supabase_auth.verify_token(auth.removeprefix("Bearer "))
    except jwt.PyJWTError:
        return False
    return True


def install_copilotkit_auth(app: FastAPI) -> None:
    """Require a valid bearer token on the copilotkit mount.

    ``add_fastapi_endpoint`` registers routes on the raw app, bypassing the
    per-route ``CurrentUser`` dependencies — without this middleware the chat
    runtime is anonymous LLM/tool invocation (cost abuse). Signature-only
    check (no DB lookup); #39 swaps the decode to Supabase JWT verification.
    """

    @app.middleware("http")
    async def copilotkit_auth(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path.startswith(COPILOTKIT_PATH) and not _bearer_token_is_valid(
            request
        ):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "code": "unauthorized",
                    "message": "Not authenticated",
                    "details": None,
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await call_next(request)


def setup_copilotkit(app: FastAPI) -> None:
    """Register LangGraph agents with CopilotKit and mount the endpoint."""
    install_copilotkit_auth(app)
    agents = [
        LangGraphAGUIAgent(
            name="fast",
            description="Simple direct LLM - fastest response, no tools",
            graph=build_fast_agent().compile(),
        ),
        LangGraphAGUIAgent(
            name="react",
            description="ReAct agent with tool calling",
            graph=build_react_agent(tool_names=["brave_search"]),
        ),
        LangGraphAGUIAgent(
            name="plan_and_execute",
            description="Plans then executes step by step",
            graph=build_plan_and_execute_agent(tool_names=["brave_search"]).compile(),
        ),
    ]

    # copilotkit's own docs pass LangGraphAGUIAgent here, but the parameter is
    # annotated as list[copilotkit.agent.Agent] upstream.
    sdk = CopilotKitRemoteEndpoint(agents=agents)  # type: ignore[arg-type]
    add_fastapi_endpoint(app, sdk, COPILOTKIT_PATH)
