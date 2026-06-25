"""Shared session/server builder for tool-level tests (test_tools_*.py)."""

from src.mcp_servers.cop_server import build_cop_server
from src.mcp_servers.session import AgentSession
from src.mcp_servers.thief_server import build_thief_server


def build_servers(grid_size=(1, 2), max_moves=25, max_barriers=5, cop_pos=(0, 0), thief_pos=(0, 1),
                   visibility_radius=2):
    cop_session = AgentSession("cop", grid_size, max_moves, max_barriers, visibility_radius)
    cop_session.start(cop_pos)
    thief_session = AgentSession("thief", grid_size, max_moves, 0, visibility_radius)
    thief_session.start(thief_pos)
    return cop_session, thief_session, build_cop_server(cop_session), build_thief_server(thief_session)
