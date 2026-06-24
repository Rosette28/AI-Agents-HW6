"""Tool-level tests: ping/echo reachability and the documented contract
(read_message/receive_message/report_location/observe_opponent/
sync_barriers/choose_action) per docs/API.md. Each server has its own
independent `AgentSession` — nothing is shared between the Cop and Thief
servers here, matching the real deployment shape.
"""

import asyncio

from fastmcp import Client

from src.mcp_servers.cop_server import build_cop_server
from src.mcp_servers.session import AgentSession
from src.mcp_servers.thief_server import build_thief_server


def _build(grid_size=(1, 2), max_moves=25, max_barriers=5, cop_pos=(0, 0), thief_pos=(0, 1),
           visibility_radius=2):
    cop_session = AgentSession("cop", grid_size, max_moves, max_barriers, visibility_radius)
    cop_session.start(cop_pos)
    thief_session = AgentSession("thief", grid_size, max_moves, 0, visibility_radius)
    thief_session.start(thief_pos)
    return cop_session, thief_session, build_cop_server(cop_session), build_thief_server(thief_session)


def test_mutual_ping_echo():
    _, _, cop_server, thief_server = _build()

    async def run():
        async with Client(cop_server) as cop, Client(thief_server) as thief:
            cop_pong = await cop.call_tool("ping")
            thief_pong = await thief.call_tool("ping")
            return cop_pong.data, thief_pong.data

    cop_pong, thief_pong = asyncio.run(run())
    assert cop_pong == {"ok": True, "agent": "cop"}
    assert thief_pong == {"ok": True, "agent": "thief"}


def test_send_message_does_not_deliver_directly_to_the_opponent():
    """Two independent servers never call each other — `send_message` is
    bookkeeping-only on the sender's own server; delivery requires the
    orchestrator to separately call `receive_message` on the recipient."""
    _, _, cop_server, thief_server = _build()

    async def run():
        async with Client(cop_server) as cop, Client(thief_server) as thief:
            send_ack = await thief.call_tool("send_message", {"text": "I am hiding nearby."})
            still_empty = await cop.call_tool("read_message")
            return send_ack.data, still_empty.data

    send_ack, still_empty = asyncio.run(run())
    assert send_ack == {"ok": True}
    assert still_empty is None


def test_receive_message_delivers_into_the_recipients_own_inbox():
    _, _, cop_server, thief_server = _build()

    async def run():
        async with Client(cop_server) as cop, Client(thief_server) as thief:
            before = await cop.call_tool("read_message")
            await cop.call_tool("receive_message", {"from_agent": "thief", "text": "I am hiding nearby."})
            after = await cop.call_tool("read_message")
            thief_inbox_untouched = await thief.call_tool("read_message")
            return before.data, after.data, thief_inbox_untouched.data

    before, after, thief_inbox_untouched = asyncio.run(run())
    assert before is None
    assert after == {"from": "thief", "text": "I am hiding nearby.", "turn": 0}
    assert thief_inbox_untouched is None


def test_report_location_returns_only_own_position():
    _, _, cop_server, thief_server = _build()

    async def run():
        async with Client(cop_server) as cop, Client(thief_server) as thief:
            cop_loc = await cop.call_tool("report_location")
            thief_loc = await thief.call_tool("report_location")
            return cop_loc.data, thief_loc.data

    cop_loc, thief_loc = asyncio.run(run())
    assert cop_loc == {"agent": "cop", "position": [0, 0]}
    assert thief_loc == {"agent": "thief", "position": [0, 1]}


def test_thief_cannot_place_barrier():
    _, _, _, thief_server = _build()

    async def run():
        async with Client(thief_server) as thief:
            return (await thief.call_tool("choose_action", {"action": {"type": "place_barrier"}})).data

    result = asyncio.run(run())
    assert result == {"accepted": False, "reason": "illegal_action_for_agent"}


def test_sync_barriers_blocks_the_other_agents_subsequent_move():
    """A barrier the Cop placed has to be explicitly synced to the Thief's
    server (no shared memory) before the Thief's own move validation can
    see it."""
    _, _, _, thief_server = _build(grid_size=(1, 2), cop_pos=(0, 0), thief_pos=(0, 1))

    async def run():
        async with Client(thief_server) as thief:
            sync_ack = await thief.call_tool("sync_barriers", {"barriers": [[0, 0]]})
            blocked = await thief.call_tool("choose_action", {"action": {"type": "move", "direction": "W"}})
            return sync_ack.data, blocked.data

    sync_ack, blocked = asyncio.run(run())
    assert sync_ack == {"ok": True, "barrier_count": 1}
    assert blocked == {"accepted": False, "reason": "blocked_by_barrier"}


def test_observe_opponent_visible_within_radius():
    """`opponent_position` is supplied by the caller (the orchestrator, in
    real use) since this server has no way to know it on its own."""
    _, _, cop_server, _ = _build(grid_size=(3, 3), cop_pos=(0, 0), thief_pos=(0, 1), visibility_radius=2)

    async def run():
        async with Client(cop_server) as cop:
            return (await cop.call_tool("observe_opponent", {"opponent_position": [0, 1]})).data

    result = asyncio.run(run())
    assert result == {"visible": True, "position": [0, 1]}


def test_observe_opponent_not_visible_outside_radius():
    _, _, cop_server, _ = _build(grid_size=(5, 5), cop_pos=(0, 0), thief_pos=(4, 4), visibility_radius=2)

    async def run():
        async with Client(cop_server) as cop:
            return (await cop.call_tool("observe_opponent", {"opponent_position": [4, 4]})).data

    result = asyncio.run(run())
    assert result == {"visible": False, "position": None}


def test_observe_opponent_with_no_position_supplied_is_not_visible():
    _, _, cop_server, _ = _build(grid_size=(3, 3), cop_pos=(0, 0), thief_pos=(0, 1), visibility_radius=2)

    async def run():
        async with Client(cop_server) as cop:
            return (await cop.call_tool("observe_opponent")).data

    result = asyncio.run(run())
    assert result == {"visible": False, "position": None}


def test_move_out_of_bounds_is_rejected_with_reason():
    _, _, cop_server, _ = _build()

    async def run():
        async with Client(cop_server) as cop:
            return (await cop.call_tool("choose_action", {"action": {"type": "move", "direction": "W"}})).data

    result = asyncio.run(run())
    assert result == {"accepted": False, "reason": "out_of_bounds"}


def test_choose_action_move_does_not_report_captured():
    """The server can't know the opponent's position, so a successful move
    response never includes a `captured` field — only the orchestrator's
    ground-truth mirror decides that."""
    _, _, cop_server, _ = _build(grid_size=(2, 2), cop_pos=(0, 0), thief_pos=(1, 1))

    async def run():
        async with Client(cop_server) as cop:
            return (await cop.call_tool("choose_action", {"action": {"type": "move", "direction": "E"}})).data

    result = asyncio.run(run())
    assert result["accepted"] is True
    assert "captured" not in result
