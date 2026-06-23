"""Bearer-token auth over real HTTP: a valid token is accepted, an invalid
or revoked one is provably rejected — per docs/prd/mcp-servers.md success
criteria. Tool-level tests use the in-memory transport (no HTTP), which
FastMCP does not enforce auth on, so this is the one place we bind a real
loopback port.
"""

import asyncio

import pytest
from fastmcp import Client

from src.mcp_servers.cop_server import build_cop_server
from src.mcp_servers.session import GameSession

_PORT = 8765
_URL = f"http://127.0.0.1:{_PORT}/mcp"


async def _with_running_server(coro_fn):
    session = GameSession((1, 2), max_moves=25, max_barriers=5)
    session.start((0, 0), (0, 1))
    server = build_cop_server(session)

    task = asyncio.create_task(server.run_http_async(host="127.0.0.1", port=_PORT, show_banner=False))
    await asyncio.sleep(0.3)  # let uvicorn bind before connecting
    try:
        return await coro_fn()
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def test_valid_token_is_accepted():
    async def call():
        async with Client(_URL, auth="test-cop-token") as client:
            return (await client.call_tool("ping")).data

    result = asyncio.run(_with_running_server(call))
    assert result == {"ok": True, "agent": "cop"}


def test_invalid_token_is_rejected():
    async def call():
        with pytest.raises(Exception):
            async with Client(_URL, auth="wrong-token") as client:
                await client.call_tool("ping")

    asyncio.run(_with_running_server(call))
