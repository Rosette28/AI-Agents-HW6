"""Manhattan-distance heuristic: Cop closes distance, Thief opens it.

Phase 3 baseline decision-maker. Exposes two interfaces over the same
distance logic so it can plug into either turn loop already in the repo:
  - `heuristic_policy(board, agent) -> action`, matching the Policy
    signature `run_subgame`/`run_game_series` (src/engine/subgame.py,
    src/engine/game.py) already use for local/offline runs.
  - `heuristic_candidate_actions(agent, board, barriers_remaining, rng)
    -> list[action]`, matching the MCP orchestrator's try-until-accepted
    pattern (src/agents/orchestrator.py), best move first.
"""

from src.engine.board import DIRECTIONS, UNKNOWN_POSITION

Action = dict
Position = tuple[int, int]


def manhattan_distance(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _positions(board, agent: str) -> tuple[Position, Position]:
    own = board.cop_pos if agent == "cop" else board.thief_pos
    opponent = board.thief_pos if agent == "cop" else board.cop_pos
    return own, opponent


def _ranked_directions(board, agent: str, rng=None) -> list[str]:
    """Legal directions from this agent's own cell, ordered best-first:
    closest-to-opponent for the Cop, farthest-from-opponent for the Thief.

    If the opponent's position is `UNKNOWN_POSITION` (no belief estimate —
    see `src.agents.belief.make_belief_board`), distance-to-opponent is
    meaningless, so this returns the legal directions in a random order
    instead (via `rng`, when given) rather than ranking against a fake
    off-board point.
    """
    own, opponent = _positions(board, agent)
    legal = list(board.legal_moves(own))
    if opponent == UNKNOWN_POSITION:
        if rng is not None:
            rng.shuffle(legal)
        return legal

    maximize = agent == "thief"

    def resulting_distance(direction: str) -> int:
        dr, dc = DIRECTIONS[direction]
        target = (own[0] + dr, own[1] + dc)
        return manhattan_distance(target, opponent)

    return sorted(legal, key=resulting_distance, reverse=maximize)


def _wants_barrier(board, agent: str, barriers_remaining: int) -> bool:
    """Cop-only: barricade its own cell when adjacent to the Thief but not
    capturing this turn. Board.place_barrier() barricades the Cop's
    *current* cell, not a target cell, so this denies that cell as an
    escape route once the Cop steps off it next turn. Never barricades on
    an unknown opponent position — adjacency can't be judged without a
    real estimate, and guessing would risk wasting one of the Cop's
    limited barrier placements.
    """
    if agent != "cop" or barriers_remaining <= 0:
        return False
    own, opponent = _positions(board, agent)
    if opponent == UNKNOWN_POSITION:
        return False
    return manhattan_distance(own, opponent) == 1


def heuristic_policy(board, agent: str) -> Action:
    """Single best action — for the local engine's Policy interface."""
    barriers_remaining = board.max_barriers - board.barriers_placed
    if _wants_barrier(board, agent, barriers_remaining):
        return {"type": "place_barrier"}
    ranked = _ranked_directions(board, agent)
    if ranked:
        return {"type": "move", "direction": ranked[0]}
    if agent == "cop" and barriers_remaining > 0:
        return {"type": "place_barrier"}
    return {"type": "move", "direction": next(iter(DIRECTIONS))}


def heuristic_candidate_actions(agent: str, board, barriers_remaining: int, rng) -> list[Action]:
    """Best-first ordered action list — for the MCP orchestrator's
    try-until-accepted loop. Always exhausts every direction as a
    fallback, so the orchestrator never starves even if the engine
    rejects the top pick for a reason the heuristic can't foresee (e.g. a
    barrier placed between when this list was built and when it's tried).
    """
    ranked = _ranked_directions(board, agent, rng=rng)
    remaining = [d for d in DIRECTIONS if d not in ranked]
    rng.shuffle(remaining)
    actions = [{"type": "move", "direction": d} for d in ranked + remaining]
    if _wants_barrier(board, agent, barriers_remaining):
        actions.insert(0, {"type": "place_barrier"})
    return actions
