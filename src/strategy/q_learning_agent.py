"""The `QLearningAgent` class: one agent's ('cop' or 'thief') Q-table,
epsilon-greedy action selection, the Bellman update, and save/load.

Split out of `src.strategy.q_learning` (which re-exports everything here)
to keep both files under the project's 150-line module limit; see that
module's docstring for the state/action/reward design this class uses.
"""

import json
import random
from pathlib import Path

from src.engine.board import UNKNOWN_POSITION
from src.strategy.heuristic import manhattan_distance
from src.strategy.q_learning_state import legal_actions, positions, state_key


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

    def state_for(self, board, visibility_radius: int | None = None) -> str:
        """State key for `board`, collapsing the opponent's position to the
        shared "unknown" bucket whenever it's not trustworthy information:

        - `board.opponent_pos == UNKNOWN_POSITION`: the belief-aware proxy
          board (`src.agents.belief.make_belief_board`) explicitly has no
          estimate — always unknown, regardless of `visibility_radius`.
        - `visibility_radius` given and the true opponent position is
          farther than that: used during training (against the real
          board, simulating the same visibility-radius mechanic the real
          game uses) so the table learns this bucket at all.

        Without `visibility_radius` (the default), only the explicit
        sentinel triggers "unknown" — the right behavior at inference time
        against a belief board, where the visibility check has already
        happened upstream in `update_belief`/`make_belief_board`; redoing
        a distance check here against an already-substituted position
        would risk mistaking a coincidentally-nearby fake coordinate for
        real information. Plain full-visibility boards (no
        `visibility_radius`, no sentinel) behave exactly as before.
        """
        own, opponent = positions(board, self.agent)
        if opponent == UNKNOWN_POSITION:
            opponent = None
        elif visibility_radius is not None and manhattan_distance(own, opponent) > visibility_radius:
            opponent = None
        return state_key(own, opponent)

    def choose_action(self, board, barriers_remaining: int,
                       visibility_radius: int | None = None) -> str | None:
        """Epsilon-greedy pick among this turn's legal actions; None if
        there are no legal actions at all (matches the Cop/Thief
        no-legal-moves edge case already handled at the engine level)."""
        actions = legal_actions(board, self.agent, barriers_remaining)
        if not actions:
            return None
        if self.rng.random() < self.epsilon:
            return self.rng.choice(actions)
        state = self.state_for(board, visibility_radius=visibility_radius)
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
