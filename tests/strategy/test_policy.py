"""Unit tests for the strategy/algorithm selector that builds the actual
Policy / candidate_actions callables used by the two turn loops."""

import random

import pytest

from src.engine.board import Board
from src.strategy.policy import build_local_policy, build_mcp_candidate_actions
from src.strategy.q_learning import QLearningAgent


def make_board():
    board = Board((5, 5), max_barriers=2)
    board.set_start_positions(cop_pos=(2, 2), thief_pos=(2, 3))
    return board


def test_build_local_policy_defaults_to_heuristic():
    policy = build_local_policy("heuristic")
    action = policy(make_board(), "cop")
    assert action["type"] in {"move", "place_barrier"}


def test_build_local_policy_q_learning_requires_an_agent():
    with pytest.raises(ValueError):
        build_local_policy("q_learning")


def test_build_local_policy_q_learning_uses_the_trained_table():
    board = make_board()
    q_agent = QLearningAgent("cop", alpha=0.1, gamma=0.9, epsilon=0.0, epsilon_decay=1.0)
    state = q_agent.state_for(board)
    q_agent._set_q(state, "E", 99.0)  # make "E" the unambiguous best pick

    policy = build_local_policy("q_learning", q_agent=q_agent)
    action = policy(board, "cop")
    assert action == {"type": "move", "direction": "E"}


def test_build_local_policy_q_learning_falls_back_to_heuristic_with_no_legal_actions():
    board = Board((1, 1), max_barriers=0)
    board.cop_pos = (0, 0)
    board.thief_pos = (0, 0)
    q_agent = QLearningAgent("cop", alpha=0.1, gamma=0.9, epsilon=0.0, epsilon_decay=1.0)

    policy = build_local_policy("q_learning", q_agent=q_agent)
    action = policy(board, "cop")
    assert action["type"] in {"move", "place_barrier"}


def test_build_mcp_candidate_actions_defaults_to_heuristic():
    candidate_fn = build_mcp_candidate_actions("heuristic")
    actions = candidate_fn("cop", make_board(), barriers_remaining=2, rng=random.Random(1))
    assert len(actions) >= 8


def test_build_mcp_candidate_actions_q_learning_puts_the_q_pick_first():
    board = make_board()
    q_agent = QLearningAgent("cop", alpha=0.1, gamma=0.9, epsilon=0.0, epsilon_decay=1.0)
    state = q_agent.state_for(board)
    q_agent._set_q(state, "E", 99.0)

    candidate_fn = build_mcp_candidate_actions("q_learning", q_agents={"cop": q_agent, "thief": q_agent})
    actions = candidate_fn("cop", board, barriers_remaining=2, rng=random.Random(1))
    assert actions[0] == {"type": "move", "direction": "E"}
    # the rest of the heuristic's ranking still follows, deduplicated
    assert len(actions) == len(set(tuple(sorted(a.items())) for a in actions))


def test_build_mcp_candidate_actions_q_learning_without_agents_falls_back_to_heuristic():
    candidate_fn = build_mcp_candidate_actions("q_learning", q_agents=None)
    actions = candidate_fn("cop", make_board(), barriers_remaining=2, rng=random.Random(1))
    assert len(actions) >= 8
