from copilotkit import CopilotKitRemoteEndpoint, LangGraphAGUIAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from fastapi import FastAPI

from app.modules.ai.agents.definitions.fast import build_fast_agent
from app.modules.ai.agents.definitions.plan_and_execute import (
    build_plan_and_execute_agent,
)
from app.modules.ai.agents.definitions.react import build_react_agent


def setup_copilotkit(app: FastAPI) -> None:
    """Register LangGraph agents with CopilotKit and mount the endpoint."""
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
    add_fastapi_endpoint(app, sdk, "/api/v1/copilotkit")
