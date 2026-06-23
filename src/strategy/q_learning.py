"""Tabular Q-Learning for the Cop and the Thief.

State: `(own_pos, opponent_pos)` on the current grid — small enough to
stay tractable up to 5x5 (≤625 state combinations per grid size, times up
to 9 actions). Action: one of the 8 directions, plus `PLACE_BARRIER` for
the Cop. Reward: shaped per-step Δ-distance toward the agent's goal, plus
a sharp terminal bonus on capture. Policy: epsilon-greedy with decay.

Q-tables are trained offline (scripts/train_q_learning.py) against the
local engine (src/engine/board.py) directly, not through the MCP
servers — thousands of training episodes over real network/tool calls
would be far slower for no benefit, since training has nothing to do
with the inter-agent NL channel (that's Phase 4). Once trained,
`QLearningAgent` plugs into either turn loop via `src/strategy/policy.py`.
"""

import json
import random
from pathlib import Path

from src.strategy.heuristic import manhattan_distance

PLACE_BARRIER = "PLACE_BARRIER"


def _positions(board, agent: str):
    own = board.cop_pos if agent == "cop" else board.thief_pos
    opponent = board.thief_pos if agent == "cop" else board.cop_pos
    return own, opponent


def _state_key(own_pos, opponent_pos) -> str:
    return f"{own_pos[0]},{own_pos[1]}|{opponent_pos[0]},{opponent_pos[1]}"


def legal_actions(board, agent: str, barriers_remaining: int) -> list[str]:
    """Legal Q-learning action tokens for `agent` in the current state."""
    own, _ = _positions(board, agent)
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


class QLearningAgent:
    """One agent's ('cop' or 'thief') Q-table and action-selection policy."""

    def __init__(self, agent: str, alpha: float, gamma: float, epsilon: float,
                 epsilon_decay: float, rng: random.Random | None = None):
        self.agent = agent
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.rng = rng or random.Random()
        self.q_table: dict[str, float] = {}

    def _q(self, state: str, action: str) -> float:
        return self.q_table.get(f"{state}::{action}", 0.0)

    def _set_q(self, state: str, action: str, value: float) -> None:
        self.q_table[f"{state}::{action}"] = value

    def state_for(self, board) -> str:
        own, opponent = _positions(board, self.agent)
        return _state_key(own, opponent)

    def choose_action(self, board, barriers_remaining: int) -> str | None:
        """Epsilon-greedy pick among this turn's legal actions; None if
        there are no legal actions at all (matches the Cop/Thief
        no-legal-moves edge case already handled at the engine level)."""
        actions = legal_actions(board, self.agent, barriers_remaining)
        if not actions:
            return None
        if self.rng.random() < self.epsilon:
            return self.rng.choice(actions)
        state = self.state_for(board)
        best_value = max(self._q(state, a) for a in actions)
        best_actions = [a for a in actions if self._q(state, a) == best_value]
        return self.rng.choice(best_actions)

    def update(self, state: str, action: str, reward: float, next_state: str,
               next_legal_actions: list[str]) -> None:
        """Bellman update:
        Q(s,a) <- Q(s,a) + alpha * [r + gamma * max_a' Q(s',a') - Q(s,a)]
        """
        old_value = self._q(state, action)
        future_value = max((self._q(next_state, a) for a in next_legal_actions), default=0.0)
        new_value = old_value + self.alpha * (reward + self.gamma * future_value - old_value)
        self._set_q(state, action, new_value)

    def decay_epsilon(self, floor: float = 0.01) -> None:
        self.epsilon = max(floor, self.epsilon * self.epsilon_decay)

    def save(self, path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"agent": self.agent, "epsilon": self.epsilon, "q_table": self.q_table}, f, indent=2)

    @classmethod
    def load(cls, path, alpha: float, gamma: float, epsilon_decay: float,
             rng: random.Random | None = None) -> "QLearningAgent":
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        instance = cls(data["agent"], alpha, gamma, data["epsilon"], epsilon_decay, rng=rng)
        instance.q_table = data["q_table"]
        return instance
