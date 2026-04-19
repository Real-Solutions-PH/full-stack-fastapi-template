from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent
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
        LangGraphAgent(
            name="fast",
            description="Simple direct LLM - fastest response, no tools",
            agent=build_fast_agent().compile(),
        ),
        LangGraphAgent(
            name="react",
            description="ReAct agent with tool calling",
            agent=build_react_agent(tool_names=["brave_search"]),
        ),
        LangGraphAgent(
            name="plan_and_execute",
            description="Plans then executes step by step",
            agent=build_plan_and_execute_agent(
                tool_names=["brave_search"]
            ).compile(),
        ),
    ]

    sdk = CopilotKitRemoteEndpoint(agents=agents)
    add_fastapi_endpoint(app, sdk, "/api/v1/copilotkit")
