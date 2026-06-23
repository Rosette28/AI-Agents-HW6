"""Cop's independent MCP server — tool contract in docs/API.md.

Owns no LLM (Client/Server separation, see docs/PLAN.md ADR-2): it only
validates and applies tool calls against the shared GameSession.
"""

from src.mcp_servers.auth import build_verifier
from src.mcp_servers.factory import build_server
from src.mcp_servers.session import GameSession


def build_cop_server(session: GameSession):
    verifier = build_verifier("COP_MCP_AUTH_TOKEN", client_id="cop-client")
    return build_server("cop-mcp-server", "cop", session, verifier)
