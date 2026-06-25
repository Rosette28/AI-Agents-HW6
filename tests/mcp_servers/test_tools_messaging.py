"""Tool-level tests: ping/echo reachability and the messaging/location
contract (read_message/receive_message/report_location) per docs/API.md.
Each server has its own independent `AgentSession` — nothing is shared
between the Cop and Thief servers here, matching the real deployment shape.
"""

import asyncio

from fastmcp import Client

from tests.mcp_servers._tool_helpers import build_servers


def test_mutual_ping_echo():
    _, _, cop_server, thief_server = build_servers()

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
    _, _, cop_server, thief_server = build_servers()

    async def run():
        async with Client(cop_server) as cop, Client(thief_server) as thief:
            send_ack = await thief.call_tool("send_message", {"text": "I am hiding nearby."})
            still_empty = await cop.call_tool("read_message")
            return send_ack.data, still_empty.data

    send_ack, still_empty = asyncio.run(run())
    assert send_ack == {"ok": True}
    assert still_empty is None


def test_receive_message_delivers_into_the_recipients_own_inbox():
    _, _, cop_server, thief_server = build_servers()

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
    _, _, cop_server, thief_server = build_servers()

    async def run():
        async with Client(cop_server) as cop, Client(thief_server) as thief:
            cop_loc = await cop.call_tool("report_location")
            thief_loc = await thief.call_tool("report_location")
            return cop_loc.data, thief_loc.data

    cop_loc, thief_loc = asyncio.run(run())
    assert cop_loc == {"agent": "cop", "position": [0, 0]}
    assert thief_loc == {"agent": "thief", "position": [0, 1]}
