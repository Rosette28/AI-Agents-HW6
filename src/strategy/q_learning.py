"""Tabular Q-Learning for the Cop and the Thief — public import surface.

Split across two modules to stay under the project's 150-line file limit;
this module just re-exports both so existing imports
(`from src.strategy.q_learning import QLearningAgent, ...`) keep working
unchanged:
  - `src.strategy.q_learning_state` — state/action/reward helpers
    (`positions`, `state_key`, `legal_actions`, `action_to_move`,
    `step_reward`, `PLACE_BARRIER`).
  - `src.strategy.q_learning_agent` — the `QLearningAgent` class itself
    (Q-table, epsilon-greedy selection, Bellman update, save/load).

See `q_learning_state`'s docstring for the full state/action/reward design,
including why the opponent's position collapses to a shared "unknown"
bucket under partial observability.
"""

from src.strategy.q_learning_agent import QLearningAgent
from src.strategy.q_learning_state import (
    PLACE_BARRIER,
    action_to_move,
    legal_actions,
    positions,
    state_key,
    step_reward,
)

__all__ = [
    "QLearningAgent",
    "PLACE_BARRIER",
    "action_to_move",
    "legal_actions",
    "positions",
    "state_key",
    "step_reward",
]
