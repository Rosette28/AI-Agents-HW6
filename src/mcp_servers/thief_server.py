"""Thief's independent MCP server — tool contract in docs/API.md.

Owns no LLM (Client/Server separation, see docs/PLAN.md ADR-2): it only
validates and applies tool calls against its own `AgentSession` — no
object shared with the Cop's server, so this is genuinely deployable on
its own, including against a foreign Cop server for the Phase 7 bonus.
Unlike the Cop server, `choose_action(type="place_barrier")` is always
rejected here.
"""

from src.mcp_servers.auth import build_verifier
from src.mcp_servers.factory import build_server
from src.mcp_servers.session import AgentSession


def build_thief_server(session: AgentSession):
    verifier = build_verifier("THIEF_MCP_AUTH_TOKEN", client_id="thief-client")
    return build_server("thief-mcp-server", "thief", session, verifier)
