"""Belief-update tests: direct observation overrides NL parsing, graceful
degradation on unreliable/empty messages, and the belief-board proxy used to
feed the existing strategy modules without leaking the true opponent
position.
"""

from unittest.mock import MagicMock

from src.agents.belief import Belief, make_belief_board, update_belief
from src.engine.board import Board


def _board(grid_size=(5, 5), max_barriers=2, cop_pos=(2, 2), thief_pos=(2, 3)):
    board = Board(grid_size, max_barriers)
    board.set_start_positions(cop_pos, thief_pos)
    return board


def test_direct_observation_overrides_message():
    llm_client = MagicMock()
    direct_observation = {"visible": True, "position": [1, 1]}
    belief = update_belief("cop", {"text": "I am far away"}, direct_observation, llm_client)
    assert belief.estimate == (1, 1)
    assert belief.confidence == "high"
    llm_client.generate_json.assert_not_called()


def test_nl_parse_used_when_not_visible():
    llm_client = MagicMock()
    llm_client.generate_json.return_value = {"row": 3, "col": 4, "confidence": "low", "note": "vague"}
    direct_observation = {"visible": False, "position": None}
    belief = update_belief("thief", {"text": "the cop is somewhere east"}, direct_observation, llm_client)
    assert belief.estimate == (3, 4)
    assert belief.confidence == "low"


def test_degrades_gracefully_on_no_message():
    llm_client = MagicMock()
    direct_observation = {"visible": False, "position": None}
    belief = update_belief("cop", None, direct_observation, llm_client)
    assert belief.estimate is None
    assert belief.confidence == "none"
    llm_client.generate_json.assert_not_called()


def test_degrades_gracefully_on_nonsensical_message():
    llm_client = MagicMock()
    llm_client.generate_json.return_value = {"row": None, "col": None, "confidence": "none", "note": "gibberish"}
    direct_observation = {"visible": False, "position": None}
    belief = update_belief("cop", {"text": "purple elephants dance"}, direct_observation, llm_client)
    assert belief.estimate is None
    assert belief.confidence == "none"


def test_degrades_gracefully_on_llm_failure():
    llm_client = MagicMock()
    llm_client.generate_json.return_value = None
    direct_observation = {"visible": False, "position": None}
    belief = update_belief("cop", {"text": "anything"}, direct_observation, llm_client)
    assert belief.estimate is None
    assert belief.confidence == "none"


def test_make_belief_board_uses_true_own_position_and_belief_estimate():
    board = _board()
    belief = Belief(estimate=(0, 0), confidence="low", note="guess")
    proxy = make_belief_board(board, "cop", belief)
    assert proxy.cop_pos == (2, 2)  # own position stays true
    assert proxy.thief_pos == (0, 0)  # opponent position is the belief


def test_make_belief_board_defaults_to_grid_center_with_no_estimate():
    board = _board(grid_size=(5, 5))
    belief = Belief(estimate=None, confidence="none", note="nothing yet")
    proxy = make_belief_board(board, "thief", belief)
    assert proxy.thief_pos == (2, 3)  # own position stays true
    assert proxy.cop_pos == (2, 2)  # grid center fallback


def test_make_belief_board_copies_barriers_not_a_new_empty_set():
    board = _board()
    board.cop_pos = (2, 2)
    board.barriers.add((1, 1))
    board.barriers_placed = 1
    belief = Belief(estimate=(0, 0), confidence="low", note="guess")
    proxy = make_belief_board(board, "cop", belief)
    assert proxy.barriers == {(1, 1)}
    assert proxy.barriers_placed == 1
