"""Unit tests for the offline Q-learning training loop
(`src.strategy.q_learning_training`), split out of
`scripts/train_q_learning.py` to keep both files under the project's
150-line limit. Verifies the loop actually runs to a winner, updates the
Q-tables, and produces a learning curve under both full-visibility and
partial-observability modes — not the real calibration run itself (that
takes thousands of episodes; see `docs/prd/strategy.md`), just that the
mechanics work.
"""

from src.engine.board import Board
from src.strategy.q_learning_agent import QLearningAgent
from src.strategy.q_learning_training import run_training_subgame, train

_Q_CONFIG = {"alpha": 0.5, "gamma": 0.9, "epsilon": 0.5, "epsilon_decay": 0.9}


def test_run_training_subgame_terminates_with_a_winner_and_updates_q_tables():
    board = Board((3, 3), max_barriers=1)
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(2, 2))
    cop_agent = QLearningAgent("cop", **_Q_CONFIG)
    thief_agent = QLearningAgent("thief", **_Q_CONFIG)

    winner = run_training_subgame(board, max_moves=25, cop_agent=cop_agent,
                                   thief_agent=thief_agent, visibility_radius=None)

    assert winner in ("cop", "thief")
    # At least one Q-value got written during the sub-game.
    assert cop_agent.q_table or thief_agent.q_table


def test_run_training_subgame_with_visibility_radius_uses_unknown_bucket():
    board = Board((5, 5), max_barriers=0)
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(4, 4))  # out of a radius-1 range
    cop_agent = QLearningAgent("cop", **_Q_CONFIG)
    thief_agent = QLearningAgent("thief", **_Q_CONFIG)

    run_training_subgame(board, max_moves=1, cop_agent=cop_agent,
                          thief_agent=thief_agent, visibility_radius=1)

    assert any(key.split("::")[0].endswith("|?") for key in cop_agent.q_table)


def test_train_produces_a_learning_curve_with_decaying_epsilon():
    cop_agent, thief_agent, curve = train(
        grid_size=(3, 3), max_moves=10, max_barriers=1, episodes=20,
        q_config=_Q_CONFIG, visibility_radius=2,
    )

    assert len(curve) >= 1
    assert curve[-1]["episode"] == 20
    assert 0.0 <= curve[-1]["cop_win_rate"] <= 1.0
    assert cop_agent.epsilon < _Q_CONFIG["epsilon"]
    assert thief_agent.epsilon < _Q_CONFIG["epsilon"]
