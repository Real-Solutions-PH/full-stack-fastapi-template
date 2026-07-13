"""AG-UI run handler streaming behavior.

test_copilotkit_transport.py proves the routes exist and are guarded; here
we drive the streaming handler itself with fake agents (no LLM): a clean
run streams the agent's events, a crashing run yields a terminal RUN_ERROR
event instead of a truncated stream, and the auth middleware's error
envelope echoes an allowed Origin (it sits outside CORSMiddleware).
"""

from collections.abc import AsyncIterator, Generator
from typing import Any

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.modules.ai.copilotkit import (
    COPILOTKIT_PATH,
    build_agui_router,
    install_copilotkit_auth,
)
from app.shared.errors import register_exception_handlers

RUN_INPUT = {
    "threadId": "thread-1",
    "runId": "run-1",
    "state": {},
    "messages": [],
    "tools": [],
    "context": [],
    "forwardedProps": {},
}


class FakeAgent:
    """Duck-typed LangGraphAGUIAgent: name/description/clone/run."""

    def __init__(self, name: str, *, fail: bool = False) -> None:
        self.name = name
        self.description = f"fake agent {name}"
        self._fail = fail

    def clone(self) -> "FakeAgent":
        return FakeAgent(self.name, fail=self._fail)

    async def run(self, input_data: Any) -> AsyncIterator[Any]:
        from ag_ui.core import EventType, RunStartedEvent

        yield RunStartedEvent(
            type=EventType.RUN_STARTED,
            thread_id=input_data.thread_id,
            run_id=input_data.run_id,
        )
        if self._fail:
            raise RuntimeError("boom")


@pytest.fixture(scope="module")
def stream_client() -> Generator[TestClient, None, None]:
    app = FastAPI()
    register_exception_handlers(app)
    install_copilotkit_auth(app)
    app.include_router(
        build_agui_router([FakeAgent("ok"), FakeAgent("broken", fail=True)])  # type: ignore[list-item]
    )
    with TestClient(app) as c:
        yield c


def test_info_route_lists_fake_agents(
    stream_client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = stream_client.get(COPILOTKIT_PATH, headers=normal_user_token_headers)
    assert r.status_code == status.HTTP_200_OK
    names = {a["name"] for a in r.json()["agents"]}
    assert names == {"ok", "broken"}


def test_run_streams_agent_events(
    stream_client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = stream_client.post(
        f"{COPILOTKIT_PATH}/agents/ok",
        headers=normal_user_token_headers,
        json=RUN_INPUT,
    )
    assert r.status_code == status.HTTP_200_OK
    assert "RUN_STARTED" in r.text
    assert "RUN_ERROR" not in r.text


def test_run_failure_emits_terminal_run_error_event(
    stream_client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = stream_client.post(
        f"{COPILOTKIT_PATH}/agents/broken",
        headers=normal_user_token_headers,
        json=RUN_INPUT,
    )
    assert r.status_code == status.HTTP_200_OK
    assert "RUN_STARTED" in r.text
    assert "RUN_ERROR" in r.text
    assert "Agent run failed" in r.text


def test_auth_envelope_echoes_allowed_origin(stream_client: TestClient) -> None:
    origin = settings.all_cors_origins[0]
    r = stream_client.get(COPILOTKIT_PATH, headers={"Origin": origin})
    assert r.status_code == status.HTTP_401_UNAUTHORIZED
    assert r.headers["Access-Control-Allow-Origin"] == origin
    assert r.headers["Access-Control-Allow-Credentials"] == "true"
    assert r.headers["WWW-Authenticate"] == "Bearer"
