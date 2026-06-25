"""State/action/reward helpers shared by `QLearningAgent`
(`src.strategy.q_learning_agent`) and the training loop
(`scripts/train_q_learning.py`).

State: `(own_pos, opponent_pos)` on the current grid, where `opponent_pos`
collapses to one shared "unknown" bucket whenever the opponent isn't
within `visibility_radius` (see `QLearningAgent.state_for`) instead of
always being an exact coordinate — what makes the table relevant under
partial observability rather than only the easier full-visibility version
of the game. State space stays tractable up to 5x5 (≤625 coordinate
combinations per grid size, plus one extra "unknown" bucket per
own-position, times up to 9 actions).

Action: one of the 8 directions, plus `PLACE_BARRIER` for the Cop.
Reward: shaped per-step Δ-distance toward the agent's goal (computed from
the *true* positions, since training has ground truth even though the
state key it's filed under may be the "unknown" bucket), plus a sharp
terminal bonus on capture.
"""

from src.strategy.heuristic import manhattan_distance

PLACE_BARRIER = "PLACE_BARRIER"
UNKNOWN_STATE_TOKEN = "?"


def positions(board, agent: str):
    own = board.cop_pos if agent == "cop" else board.thief_pos
    opponent = board.thief_pos if agent == "cop" else board.cop_pos
    return own, opponent


def state_key(own_pos, opponent_pos) -> str:
    if opponent_pos is None:
        return f"{own_pos[0]},{own_pos[1]}|{UNKNOWN_STATE_TOKEN}"
    return f"{own_pos[0]},{own_pos[1]}|{opponent_pos[0]},{opponent_pos[1]}"


def legal_actions(board, agent: str, barriers_remaining: int) -> list[str]:
    """Legal Q-learning action tokens for `agent` in the current state."""
    own, _ = positions(board, agent)
    actions = list(board.legal_moves(own))
    if agent == "cop" and barriers_remaining > 0:
        actions.append(PLACE_BARRIER)
    return actions


def action_to_move(action: str) -> dict:
    """Convert a Q-learning action token to the engine's action dict."""
    if action == PLACE_BARRIER:
        return {"type": "place_barrier"}
    return {"type": "move", "direction": action}


def step_reward(agent: str, own_before, own_after, opponent_pos, captured: bool) -> float:
    """Per-step shaped reward: Δdistance toward the agent's goal, plus a
    sharp terminal bonus on capture. Survival is the only other terminal
    outcome, but it isn't visible from inside a single step — the
    training loop in scripts/train_q_learning.py only ever calls this with
    `captured=True` or `False`, and relies on per-step shaping (not a
    survival bonus) to teach the Thief to keep its distance.
    """
    if captured:
        return 50.0 if agent == "cop" else -50.0
    before = manhattan_distance(own_before, opponent_pos)
    after = manhattan_distance(own_after, opponent_pos)
    delta = before - after  # positive = agent got closer to the opponent
    return float(delta) if agent == "cop" else float(-delta)
