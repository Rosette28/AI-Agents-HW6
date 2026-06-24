"""Phase 5: the orchestrator must be able to drive a sub-game against an
already-deployed remote server (not just local in-process ones) — required
for a real graded cloud run. Proves it end to end by binding the Cop and
Thief servers to real loopback HTTP ports (standing in for a real cloud
deployment) and passing their URLs as `cop_endpoint`/`thief_endpoint`.
"""

import asyncio
import random

import pytest

from src.agents.orchestrator import run_subgame_via_mcp
from src.mcp_servers.cop_server import build_cop_server
from src.mcp_servers.session import AgentSession
from src.mcp_servers.thief_server import build_thief_server

_COP_PORT = 8771
_THIEF_PORT = 8772


@pytest.fixture(autouse=True)
def _mcp_auth_tokens(monkeypatch):
    monkeypatch.setenv("COP_MCP_AUTH_TOKEN", "test-cop-token")
    monkeypatch.setenv("THIEF_MCP_AUTH_TOKEN", "test-thief-token")


async def _with_remote_servers(coro_fn):
    cop_session = AgentSession("cop", (3, 3), max_moves=25, max_barriers=5)
    thief_session = AgentSession("thief", (3, 3), max_moves=25, max_barriers=0)
    cop_server = build_cop_server(cop_session)
    thief_server = build_thief_server(thief_session)

    cop_task = asyncio.create_task(
        cop_server.run_http_async(host="127.0.0.1", port=_COP_PORT, show_banner=False))
    thief_task = asyncio.create_task(
        thief_server.run_http_async(host="127.0.0.1", port=_THIEF_PORT, show_banner=False))
    await asyncio.sleep(0.3)  # let uvicorn bind before connecting
    try:
        return await coro_fn()
    finally:
        for task in (cop_task, thief_task):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


def test_subgame_runs_end_to_end_against_remote_http_servers():
    async def run():
        return await run_subgame_via_mcp(
            (3, 3), max_moves=25, max_barriers=5, cop_pos=(0, 0), thief_pos=(2, 2),
            rng=random.Random(3),
            cop_endpoint={"url": f"http://127.0.0.1:{_COP_PORT}/mcp", "token": "test-cop-token"},
            thief_endpoint={"url": f"http://127.0.0.1:{_THIEF_PORT}/mcp", "token": "test-thief-token"},
        )

    result = asyncio.run(_with_remote_servers(run))
    assert result["winner"] in {"cop", "thief"}
    assert 1 <= result["moves_taken"] <= 25


def test_remote_server_session_resets_cleanly_between_sub_games():
    """A long-lived remote server must serve a fresh sub-game correctly
    even though its session already holds state from a previous one."""
    async def run():
        first = await run_subgame_via_mcp(
            (3, 3), max_moves=25, max_barriers=5, cop_pos=(0, 0), thief_pos=(2, 2),
            rng=random.Random(1),
            cop_endpoint={"url": f"http://127.0.0.1:{_COP_PORT}/mcp", "token": "test-cop-token"},
            thief_endpoint={"url": f"http://127.0.0.1:{_THIEF_PORT}/mcp", "token": "test-thief-token"},
        )
        second = await run_subgame_via_mcp(
            (3, 3), max_moves=25, max_barriers=5, cop_pos=(2, 2), thief_pos=(0, 0),
            rng=random.Random(2),
            cop_endpoint={"url": f"http://127.0.0.1:{_COP_PORT}/mcp", "token": "test-cop-token"},
            thief_endpoint={"url": f"http://127.0.0.1:{_THIEF_PORT}/mcp", "token": "test-thief-token"},
        )
        return first, second

    first, second = asyncio.run(_with_remote_servers(run))
    assert first["winner"] in {"cop", "thief"}
    assert second["winner"] in {"cop", "thief"}
    assert second["barriers_placed"] <= 5  # the cap, not an accumulation across both sub-games
