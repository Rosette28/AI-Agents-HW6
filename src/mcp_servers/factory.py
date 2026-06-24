"""Shared tool-registration logic for the Cop and Thief MCP servers.

Both servers expose the same tool contract (docs/API.md); the only behavior
difference is that `place_barrier` is rejected for the Thief. Factoring this
out keeps cop_server.py/thief_server.py thin and avoids duplicating the tool
bodies (DRY) while still giving each agent its own independent FastMCP
server instance bound to its own independent `AgentSession`, per the
assignment's "two independent servers" requirement — there is no object
shared between the two servers; the orchestrator is the only thing that
talks to both. See `src/agents/orchestrator.py` for how messages get
relayed and barriers get synced between two servers that never call each
other directly.
"""

from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

from src.mcp_servers.session import Agent, AgentSession
from src.strategy.heuristic import manhattan_distance


def build_server(name: str, agent: Agent, session: AgentSession, verifier: StaticTokenVerifier) -> FastMCP:
    """Construct a FastMCP server for `agent` ('cop' or 'thief') bound to its
    own `session` — never the opponent's."""
    server = FastMCP(name=name, auth=verifier)

    @server.tool
    def ping() -> dict:
        """Trivial reachability check — used for the mutual ping/echo test."""
        return {"ok": True, "agent": agent}

    @server.tool
    def read_message() -> dict | None:
        """Return the most recent NL message addressed to this agent, if any."""
        return session.latest_message()

    @server.tool
    def send_message(text: str) -> dict:
        """Records this agent's own outgoing message. Actual delivery to
        the opponent is the orchestrator's job (`receive_message` on the
        opponent's own server) — two independently-deployed servers never
        call each other directly.
        """
        return {"ok": True}

    @server.tool
    def receive_message(from_agent: str, text: str) -> dict:
        """Orchestrator-relayed delivery of the opponent's message into
        this agent's own inbox."""
        entry = session.deliver_message(from_agent, text)
        return {"ok": True, "turn": entry["turn"]}

    @server.tool
    def report_location() -> dict:
        """Internal/scoring-only: this agent's own exact position.

        Must never be relayed to the opponent — only ever called by the
        orchestrator for its own bookkeeping.
        """
        pos = session.position
        return {"agent": agent, "position": list(pos) if pos else None}

    @server.tool
    def observe_opponent(opponent_position: list[int] | None = None) -> dict:
        """Partial observation: whether the opponent is within
        `visibility_radius` of this agent's own position.

        `opponent_position` is supplied by the orchestrator (the only party
        with legitimate access to both agents' true positions) — this
        server never knows the opponent's position on its own.
        """
        if opponent_position is None or session.position is None:
            return {"visible": False, "position": None}
        opponent_pos = tuple(opponent_position)
        if manhattan_distance(session.position, opponent_pos) <= session.visibility_radius:
            return {"visible": True, "position": list(opponent_pos)}
        return {"visible": False, "position": None}

    @server.tool
    def sync_barriers(barriers: list[list[int]]) -> dict:
        """Keeps this server's local barrier set in sync with barriers
        placed by the Cop (Cop-only action) — relevant on the Thief's
        server, since barriers block both agents but only the Cop's own
        server learns about a new one directly from `place_barrier`.
        Idempotent full overwrite, called by the orchestrator right after
        every successful barrier placement.
        """
        session.sync_barriers(barriers)
        return {"ok": True, "barrier_count": len(session.barriers)}

    @server.tool
    def choose_action(action: dict) -> dict:
        """Move or (Cop-only) place_barrier; validated and applied against
        this agent's own session. Never reports `captured` — only the
        orchestrator, which can see both agents' true positions, decides
        that.
        """
        action_type = action.get("type")
        if action_type == "move":
            result = session.move(action.get("direction", ""))
        elif action_type == "place_barrier":
            if agent != "cop":
                return {"accepted": False, "reason": "illegal_action_for_agent"}
            result = session.place_barrier()
        else:
            return {"accepted": False, "reason": "unknown_action_type"}

        if result.get("accepted"):
            session.advance_round()
            result["moves_remaining"] = session.moves_remaining()
            if action_type == "place_barrier" or agent == "cop":
                result["barriers_remaining"] = session.max_barriers - session.barriers_placed
        return result

    return server
