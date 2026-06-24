"""Cop's independent MCP server — tool contract in docs/API.md.

Owns no LLM (Client/Server separation, see docs/PLAN.md ADR-2): it only
validates and applies tool calls against its own `AgentSession` — no
object shared with the Thief's server, so this is genuinely deployable on
its own, including against a foreign Thief server for the Phase 7 bonus.
"""

from src.mcp_servers.auth import build_verifier
from src.mcp_servers.factory import build_server
from src.mcp_servers.session import AgentSession


def build_cop_server(session: AgentSession):
    verifier = build_verifier("COP_MCP_AUTH_TOKEN", client_id="cop-client")
    return build_server("cop-mcp-server", "cop", session, verifier)
