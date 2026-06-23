"""Thief's independent MCP server — tool contract in docs/API.md.

Owns no LLM (Client/Server separation, see docs/PLAN.md ADR-2): it only
validates and applies tool calls against the shared GameSession. Unlike the
Cop server, `choose_action(type="place_barrier")` is always rejected here.
"""

from src.mcp_servers.auth import build_verifier
from src.mcp_servers.factory import build_server
from src.mcp_servers.session import GameSession


def build_thief_server(session: GameSession):
    verifier = build_verifier("THIEF_MCP_AUTH_TOKEN", client_id="thief-client")
    return build_server("thief-mcp-server", "thief", session, verifier)
