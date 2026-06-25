"""Tool-level tests: the action/observation contract (choose_action,
observe_opponent, sync_barriers) per docs/API.md. Each server has its own
independent `AgentSession` — nothing is shared between the Cop and Thief
servers here, matching the real deployment shape.
"""

import asyncio

from fastmcp import Client

from tests.mcp_servers._tool_helpers import build_servers


def test_thief_cannot_place_barrier():
    _, _, _, thief_server = build_servers()

    async def run():
        async with Client(thief_server) as thief:
            return (await thief.call_tool("choose_action", {"action": {"type": "place_barrier"}})).data

    result = asyncio.run(run())
    assert result == {"accepted": False, "reason": "illegal_action_for_agent"}


def test_sync_barriers_blocks_the_other_agents_subsequent_move():
    """A barrier the Cop placed has to be explicitly synced to the Thief's
    server (no shared memory) before the Thief's own move validation can
    see it."""
    _, _, _, thief_server = build_servers(grid_size=(1, 2), cop_pos=(0, 0), thief_pos=(0, 1))

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
    _, _, cop_server, _ = build_servers(grid_size=(3, 3), cop_pos=(0, 0), thief_pos=(0, 1), visibility_radius=2)

    async def run():
        async with Client(cop_server) as cop:
            return (await cop.call_tool("observe_opponent", {"opponent_position": [0, 1]})).data

    result = asyncio.run(run())
    assert result == {"visible": True, "position": [0, 1]}


def test_observe_opponent_not_visible_outside_radius():
    _, _, cop_server, _ = build_servers(grid_size=(5, 5), cop_pos=(0, 0), thief_pos=(4, 4), visibility_radius=2)

    async def run():
        async with Client(cop_server) as cop:
            return (await cop.call_tool("observe_opponent", {"opponent_position": [4, 4]})).data

    result = asyncio.run(run())
    assert result == {"visible": False, "position": None}


def test_observe_opponent_with_no_position_supplied_is_not_visible():
    _, _, cop_server, _ = build_servers(grid_size=(3, 3), cop_pos=(0, 0), thief_pos=(0, 1), visibility_radius=2)

    async def run():
        async with Client(cop_server) as cop:
            return (await cop.call_tool("observe_opponent")).data

    result = asyncio.run(run())
    assert result == {"visible": False, "position": None}


def test_move_out_of_bounds_is_rejected_with_reason():
    _, _, cop_server, _ = build_servers()

    async def run():
        async with Client(cop_server) as cop:
            return (await cop.call_tool("choose_action", {"action": {"type": "move", "direction": "W"}})).data

    result = asyncio.run(run())
    assert result == {"accepted": False, "reason": "out_of_bounds"}


def test_choose_action_move_does_not_report_captured():
    """The server can't know the opponent's position, so a successful move
    response never includes a `captured` field — only the orchestrator's
    ground-truth mirror decides that."""
    _, _, cop_server, _ = build_servers(grid_size=(2, 2), cop_pos=(0, 0), thief_pos=(1, 1))

    async def run():
        async with Client(cop_server) as cop:
            return (await cop.call_tool("choose_action", {"action": {"type": "move", "direction": "E"}})).data

    result = asyncio.run(run())
    assert result["accepted"] is True
    assert "captured" not in result
