"""Shared sub-game session: the single authoritative Board plus the two
agents' message inboxes.

Both the Cop and Thief MCP servers apply actions against this one Board
(matching the Container diagram in docs/PLAN.md — both servers call the same
Game Engine), but each server only ever reads its *own* inbox. The opponent's
inbox is filled exclusively by the other server's `send_message`, never read
directly — that keeps the natural-language channel as the only coupling
between the two agents, preserving partial observability.
"""

from src.engine.board import Board

Agent = str  # "cop" | "thief"


class GameSession:
    """Engine + per-agent inboxes + move counter for one sub-game."""

    def __init__(self, grid_size: tuple[int, int], max_moves: int, max_barriers: int):
        self.board = Board(grid_size, max_barriers)
        self.max_moves = max_moves
        self.move_number = 0
        self.inboxes: dict[Agent, list[dict]] = {"cop": [], "thief": []}

    def start(self, cop_pos: tuple[int, int], thief_pos: tuple[int, int]) -> None:
        self.board.set_start_positions(cop_pos, thief_pos)

    def deliver_message(self, to_agent: Agent, from_agent: Agent, text: str) -> dict:
        """Append an NL message to `to_agent`'s inbox; returns the stored entry."""
        entry = {"from": from_agent, "text": text, "turn": self.move_number}
        self.inboxes[to_agent].append(entry)
        return entry

    def latest_message(self, agent: Agent) -> dict | None:
        """Most recent message addressed to `agent`, or None if its inbox is empty."""
        inbox = self.inboxes[agent]
        return inbox[-1] if inbox else None

    def moves_remaining(self) -> int:
        return max(self.max_moves - self.move_number, 0)

    def advance_round(self) -> None:
        """Call once both agents have acted in a round (mirrors
        `run_subgame`'s loop variable in src/engine/subgame.py)."""
        self.move_number += 1
