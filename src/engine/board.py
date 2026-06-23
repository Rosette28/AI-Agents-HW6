"""Board state machine — positions, barriers, and movement validation.

Pure game rules, no LLM/networking. Grid size and max_barriers always come
from the caller (ultimately config.yaml) — never hardcoded here.
"""

Position = tuple[int, int]

# 8-direction offsets as (delta_row, delta_col).
DIRECTIONS: dict[str, tuple[int, int]] = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
    "NE": (-1, 1),
    "NW": (-1, -1),
    "SE": (1, 1),
    "SW": (1, -1),
}


class Board:
    """Authoritative state for one sub-game: positions, barriers, move count."""

    def __init__(self, grid_size: tuple[int, int], max_barriers: int):
        """grid_size = (rows, cols); max_barriers = Cop's per-sub-game cap."""
        self.rows, self.cols = grid_size
        self.max_barriers = max_barriers
        self.cop_pos: Position | None = None
        self.thief_pos: Position | None = None
        self.barriers: set[Position] = set()
        self.barriers_placed = 0

    def set_start_positions(self, cop_pos: Position, thief_pos: Position) -> None:
        """Place both agents; raises if they start on the same cell."""
        if cop_pos == thief_pos:
            raise ValueError("Cop and Thief cannot start on the same cell")
        self.cop_pos = cop_pos
        self.thief_pos = thief_pos

    def in_bounds(self, pos: Position) -> bool:
        r, c = pos
        return 0 <= r < self.rows and 0 <= c < self.cols

    def legal_moves(self, pos: Position) -> list[str]:
        """Directions from pos that land in-bounds and off any barrier."""
        legal = []
        for name, (dr, dc) in DIRECTIONS.items():
            target = (pos[0] + dr, pos[1] + dc)
            if self.in_bounds(target) and target not in self.barriers:
                legal.append(name)
        return legal

    def move(self, agent: str, direction: str) -> dict:
        """Move 'cop' or 'thief' one step. Returns a result dict with
        accepted/new_position/captured, or accepted=False + reason.
        """
        pos = self.cop_pos if agent == "cop" else self.thief_pos
        if direction not in DIRECTIONS:
            return {"accepted": False, "reason": "unknown_direction"}
        dr, dc = DIRECTIONS[direction]
        target = (pos[0] + dr, pos[1] + dc)
        if not self.in_bounds(target):
            return {"accepted": False, "reason": "out_of_bounds"}
        if target in self.barriers:
            return {"accepted": False, "reason": "blocked_by_barrier"}
        if agent == "cop":
            self.cop_pos = target
        else:
            self.thief_pos = target
        captured = self.cop_pos == self.thief_pos
        return {"accepted": True, "new_position": target, "captured": captured}

    def place_barrier(self) -> dict:
        """Cop-only: barricade the Cop's current cell. Blocks both agents."""
        if self.barriers_placed >= self.max_barriers:
            return {"accepted": False, "reason": "no_barriers_remaining"}
        self.barriers.add(self.cop_pos)
        self.barriers_placed += 1
        return {
            "accepted": True,
            "barriers_remaining": self.max_barriers - self.barriers_placed,
        }

    def is_captured(self) -> bool:
        return self.cop_pos == self.thief_pos
