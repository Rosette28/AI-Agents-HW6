"""Tool-level tests: ping/echo reachability and the documented contract
(read_message/send_message/report_location/choose_action) per docs/API.md.
"""

import asyncio

from fastmcp import Client

from src.mcp_servers.cop_server import build_cop_server
from src.mcp_servers.session import GameSession
from src.mcp_servers.thief_server import build_thief_server


def _build(grid_size=(1, 2), max_moves=25, max_barriers=5, cop_pos=(0, 0), thief_pos=(0, 1)):
    session = GameSession(grid_size, max_moves, max_barriers)
    session.start(cop_pos, thief_pos)
    return session, build_cop_server(session), build_thief_server(session)


def test_mutual_ping_echo():
    _, cop_server, thief_server = _build()

    async def run():
        async with Client(cop_server) as cop, Client(thief_server) as thief:
            cop_pong = await cop.call_tool("ping")
            thief_pong = await thief.call_tool("ping")
            return cop_pong.data, thief_pong.data

    cop_pong, thief_pong = asyncio.run(run())
    assert cop_pong == {"ok": True, "agent": "cop"}
    assert thief_pong == {"ok": True, "agent": "thief"}


def test_message_relay_is_not_visible_until_sent():
    _, cop_server, thief_server = _build()

    async def run():
        async with Client(cop_server) as cop, Client(thief_server) as thief:
            before = await cop.call_tool("read_message")
            await thief.call_tool("send_message", {"text": "I am hiding nearby."})
            after = await cop.call_tool("read_message")
            return before.data, after.data

    before, after = asyncio.run(run())
    assert before is None
    assert after == {"from": "thief", "text": "I am hiding nearby.", "turn": 0}


def test_report_location_returns_only_own_position():
    _, cop_server, thief_server = _build()

    async def run():
        async with Client(cop_server) as cop, Client(thief_server) as thief:
            cop_loc = await cop.call_tool("report_location")
            thief_loc = await thief.call_tool("report_location")
            return cop_loc.data, thief_loc.data

    cop_loc, thief_loc = asyncio.run(run())
    assert cop_loc == {"agent": "cop", "position": [0, 0]}
    assert thief_loc == {"agent": "thief", "position": [0, 1]}


def test_thief_cannot_place_barrier():
    _, _, thief_server = _build()

    async def run():
        async with Client(thief_server) as thief:
            return (await thief.call_tool("choose_action", {"action": {"type": "place_barrier"}})).data

    result = asyncio.run(run())
    assert result == {"accepted": False, "reason": "illegal_action_for_agent"}


def test_move_out_of_bounds_is_rejected_with_reason():
    _, cop_server, _ = _build()

    async def run():
        async with Client(cop_server) as cop:
            return (await cop.call_tool("choose_action", {"action": {"type": "move", "direction": "W"}})).data

    result = asyncio.run(run())
    assert result == {"accepted": False, "reason": "out_of_bounds"}
