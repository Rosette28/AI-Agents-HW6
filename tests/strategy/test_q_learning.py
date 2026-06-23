"""Unit tests for tabular Q-Learning: the Bellman update produces the exact
expected Q-value for a known transition, epsilon-greedy action selection
statistically respects the configured epsilon, and Q-tables survive a
save/load round-trip."""

import random

import pytest

from src.engine.board import Board
from src.strategy.q_learning import QLearningAgent, legal_actions


def test_bellman_update_matches_hand_computed_value():
    agent = QLearningAgent("cop", alpha=0.5, gamma=0.9, epsilon=0.0, epsilon_decay=1.0)
    agent._set_q("s1", "E", 2.0)
    agent._set_q("s2", "N", 10.0)
    agent._set_q("s2", "S", 4.0)

    agent.update(state="s1", action="E", reward=1.0, next_state="s2", next_legal_actions=["N", "S"])

    # Q(s,a) <- Q(s,a) + alpha * (r + gamma * max_a' Q(s',a') - Q(s,a))
    # = 2.0 + 0.5 * (1.0 + 0.9 * 10.0 - 2.0) = 2.0 + 0.5 * 8.0 = 6.0
    assert agent._q("s1", "E") == pytest.approx(6.0)


def test_bellman_update_with_no_future_actions_uses_zero_future_value():
    agent = QLearningAgent("thief", alpha=0.1, gamma=0.9, epsilon=0.0, epsilon_decay=1.0)
    agent.update(state="terminal_prev", action="N", reward=-50.0, next_state="terminal", next_legal_actions=[])
    # Q <- 0 + 0.1 * (-50 + 0.9*0 - 0) = -5.0
    assert agent._q("terminal_prev", "N") == pytest.approx(-5.0)


def test_epsilon_greedy_always_exploits_when_epsilon_is_zero():
    board = Board((5, 5), max_barriers=0)
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(4, 4))
    agent = QLearningAgent("cop", alpha=0.1, gamma=0.9, epsilon=0.0, epsilon_decay=1.0, rng=random.Random(1))
    state = agent.state_for(board)
    agent._set_q(state, "S", 5.0)  # make "S" the clear best action
    for action in legal_actions(board, "cop", 0):
        if action != "S":
            agent._set_q(state, action, -1.0)

    picks = {agent.choose_action(board, 0) for _ in range(20)}
    assert picks == {"S"}


def test_epsilon_greedy_explores_at_the_configured_rate_statistically():
    board = Board((5, 5), max_barriers=0)
    # Center cell so all 8 directions are legal, making the expected
    # explore-but-still-pick-S probability a clean 1/8.
    board.set_start_positions(cop_pos=(2, 2), thief_pos=(4, 4))
    agent = QLearningAgent("cop", alpha=0.1, gamma=0.9, epsilon=0.3, epsilon_decay=1.0, rng=random.Random(42))
    state = agent.state_for(board)
    legal = legal_actions(board, "cop", 0)
    assert len(legal) == 8
    agent._set_q(state, "S", 5.0)
    for action in legal:
        if action != "S":
            agent._set_q(state, action, -1.0)

    trials = 8000
    non_greedy_picks = sum(1 for _ in range(trials) if agent.choose_action(board, 0) != "S")
    observed_rate = non_greedy_picks / trials
    # With epsilon=0.3, a random explore pick lands on "S" with prob 1/8
    # (one of 8 legal directions), so non-greedy-looking picks should be
    # close to epsilon * (7/8), not exactly epsilon.
    expected_rate = 0.3 * (7 / 8)
    assert abs(observed_rate - expected_rate) < 0.025


def test_decay_epsilon_respects_floor():
    agent = QLearningAgent("cop", alpha=0.1, gamma=0.9, epsilon=0.02, epsilon_decay=0.5)
    agent.decay_epsilon(floor=0.01)
    assert agent.epsilon == pytest.approx(0.01)


def test_save_and_load_round_trip(tmp_path):
    agent = QLearningAgent("thief", alpha=0.1, gamma=0.9, epsilon=0.15, epsilon_decay=0.99)
    agent._set_q("1,1|2,2", "N", 3.5)
    path = tmp_path / "thief_qtable.json"
    agent.save(path)

    loaded = QLearningAgent.load(path, alpha=0.1, gamma=0.9, epsilon_decay=0.99)
    assert loaded.agent == "thief"
    assert loaded.epsilon == pytest.approx(0.15)
    assert loaded._q("1,1|2,2", "N") == pytest.approx(3.5)


def test_legal_actions_includes_barrier_only_for_cop_with_barriers_remaining():
    board = Board((5, 5), max_barriers=5)
    board.set_start_positions(cop_pos=(2, 2), thief_pos=(2, 3))
    assert "PLACE_BARRIER" in legal_actions(board, "cop", barriers_remaining=1)
    assert "PLACE_BARRIER" not in legal_actions(board, "cop", barriers_remaining=0)
    assert "PLACE_BARRIER" not in legal_actions(board, "thief", barriers_remaining=1)
