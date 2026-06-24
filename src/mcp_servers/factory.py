"""Shared tool-registration logic for the Cop and Thief MCP servers.

Both servers expose the same tool contract (docs/API.md); the only behavior
difference is that `place_barrier` is rejected for the Thief. Factoring this
out keeps cop_server.py/thief_server.py thin and avoids duplicating the tool
bodies (DRY) while still giving each agent its own independent FastMCP
server instance, per the assignment's "two independent servers" requirement.
"""

from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

from src.mcp_servers.session import Agent, GameSession
from src.strategy.heuristic import manhattan_distance


def build_server(name: str, agent: Agent, session: GameSession, verifier: StaticTokenVerifier) -> FastMCP:
    """Construct a FastMCP server for `agent` ('cop' or 'thief') bound to `session`."""
    opponent: Agent = "thief" if agent == "cop" else "cop"
    server = FastMCP(name=name, auth=verifier)

    @server.tool
    def ping() -> dict:
        """Trivial reachability check — used for the mutual ping/echo test."""
        return {"ok": True, "agent": agent}

    @server.tool
    def read_message() -> dict | None:
        """Return the most recent NL message sent by the opponent, if any."""
        return session.latest_message(agent)

    @server.tool
    def send_message(text: str) -> dict:
        """Relay an NL message to the opponent's server inbox."""
        entry = session.deliver_message(to_agent=opponent, from_agent=agent, text=text)
        return {"ok": True, "turn": entry["turn"]}

    @server.tool
    def report_location() -> dict:
        """Internal/scoring-only: this agent's own exact position.

        Must never be relayed to the opponent — only ever called by this
        agent's own orchestrator for its own bookkeeping.
        """
        pos = session.board.cop_pos if agent == "cop" else session.board.thief_pos
        return {"agent": agent, "position": list(pos) if pos else None}

    @server.tool
    def observe_opponent() -> dict:
        """Partial observation: the opponent's true position, but only if
        within `session.visibility_radius` of this agent's own position —
        otherwise the agent must rely on the NL channel alone.
        """
        own_pos = session.board.cop_pos if agent == "cop" else session.board.thief_pos
        opponent_pos = session.board.thief_pos if agent == "cop" else session.board.cop_pos
        if manhattan_distance(own_pos, opponent_pos) <= session.visibility_radius:
            return {"visible": True, "position": list(opponent_pos)}
        return {"visible": False, "position": None}

    @server.tool
    def choose_action(action: dict) -> dict:
        """Move or (Cop-only) place_barrier; validated and applied to the engine."""
        action_type = action.get("type")
        if action_type == "move":
            result = session.board.move(agent, action.get("direction", ""))
        elif action_type == "place_barrier":
            if agent != "cop":
                return {"accepted": False, "reason": "illegal_action_for_agent"}
            result = session.board.place_barrier()
        else:
            return {"accepted": False, "reason": "unknown_action_type"}

        if result.get("accepted"):
            result["moves_remaining"] = session.moves_remaining()
            if action_type == "move":
                result["captured"] = session.board.is_captured()
            if action_type == "place_barrier" or agent == "cop":
                result["barriers_remaining"] = (
                    session.board.max_barriers - session.board.barriers_placed
                )
        return result

    return server
