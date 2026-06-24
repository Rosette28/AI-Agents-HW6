"""Per-agent session: everything ONE MCP server needs to validate its own
agent's moves, with no shared object between the Cop and Thief servers.

This is what makes the two servers genuinely independently-deployable
(including against a totally separate partner group's server for the
Phase 7 bonus) rather than two API surfaces over one shared Python object
in a single process. Movement legality only needs this agent's own
position plus the barrier set (synced explicitly via `sync_barriers`, see
docs/API.md) — never the opponent's position. Anything that legitimately
needs both agents' true positions (capture detection, visibility checks)
is the orchestrator's job, not this server's — see
`src/agents/orchestrator.py`.
"""

from src.engine.board import DIRECTIONS

Agent = str  # "cop" | "thief"
Position = tuple[int, int]


class AgentSession:
    """Authoritative state for ONE agent's own server: position, barriers
    known to this server, inbox, and move counter."""

    def __init__(self, agent: Agent, grid_size: tuple[int, int], max_moves: int,
                 max_barriers: int = 0, visibility_radius: int = 2):
        """`max_barriers` is 0 for the Thief — it can never place one, so it
        has nothing to cap. `visibility_radius` (cells, Manhattan) is the
        Phase 4 partial-observability cutoff for `observe_opponent`.
        """
        self.agent = agent
        self.rows, self.cols = grid_size
        self.max_moves = max_moves
        self.max_barriers = max_barriers
        self.visibility_radius = visibility_radius
        self.position: Position | None = None
        self.barriers: set[Position] = set()
        self.barriers_placed = 0
        self.move_number = 0
        self.inbox: list[dict] = []

    def start(self, position: Position) -> None:
        """(Re)initialize this session for a new sub-game: position,
        barriers, inbox, and move counter all reset. Safe to call more
        than once on the same server — a long-lived deployed server plays
        many sub-games in one series, each needing a clean slate (exposed
        as the `start_subgame` tool, see factory.py)."""
        self.position = position
        self.barriers = set()
        self.barriers_placed = 0
        self.move_number = 0
        self.inbox = []

    def in_bounds(self, pos: Position) -> bool:
        r, c = pos
        return 0 <= r < self.rows and 0 <= c < self.cols

    def move(self, direction: str) -> dict:
        """Validate and apply a move against this server's own
        position/barriers/bounds. Never reports `captured` — this server
        has no way to know the opponent's position; the orchestrator
        decides that from its own ground-truth mirror.
        """
        if direction not in DIRECTIONS:
            return {"accepted": False, "reason": "unknown_direction"}
        dr, dc = DIRECTIONS[direction]
        target = (self.position[0] + dr, self.position[1] + dc)
        if not self.in_bounds(target):
            return {"accepted": False, "reason": "out_of_bounds"}
        if target in self.barriers:
            return {"accepted": False, "reason": "blocked_by_barrier"}
        self.position = target
        return {"accepted": True, "new_position": target}

    def place_barrier(self) -> dict:
        """Cop-only (enforced by the caller, see factory.py): barricade this
        agent's current cell."""
        if self.barriers_placed >= self.max_barriers:
            return {"accepted": False, "reason": "no_barriers_remaining"}
        self.barriers.add(self.position)
        self.barriers_placed += 1
        return {"accepted": True, "barriers_remaining": self.max_barriers - self.barriers_placed}

    def sync_barriers(self, barriers: list[Position]) -> None:
        """Overwrite this server's local barrier set — called by the
        orchestrator on the *other* agent's server right after a successful
        `place_barrier`, since barriers must block both agents but only the
        Cop's own server learns about a new one directly."""
        self.barriers = {tuple(b) for b in barriers}

    def deliver_message(self, from_agent: Agent, text: str) -> dict:
        """Append a message to this agent's own inbox. Called by the
        orchestrator (relaying the opponent's message), never by the
        opponent's server directly — servers never talk to each other."""
        entry = {"from": from_agent, "text": text, "turn": self.move_number}
        self.inbox.append(entry)
        return entry

    def latest_message(self) -> dict | None:
        return self.inbox[-1] if self.inbox else None

    def moves_remaining(self) -> int:
        return max(self.max_moves - self.move_number, 0)

    def advance_round(self) -> None:
        """Call once this agent has acted — informational only (feeds
        `moves_remaining` back to the agent); the orchestrator's own loop
        is what actually enforces `max_moves`/survival."""
        self.move_number += 1
