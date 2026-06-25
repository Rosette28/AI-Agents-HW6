"""Unit tests for the Manhattan-distance heuristic: Cop closes distance,
Thief opens it, and the Cop barricades when adjacent."""

import random

from src.engine.board import UNKNOWN_POSITION, Board
from src.strategy.heuristic import (
    heuristic_candidate_actions,
    heuristic_policy,
    manhattan_distance,
)


def test_manhattan_distance():
    assert manhattan_distance((0, 0), (3, 4)) == 7
    assert manhattan_distance((2, 2), (2, 2)) == 0


def test_cop_policy_moves_toward_thief():
    board = Board((5, 5), max_barriers=0)
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(4, 4))
    action = heuristic_policy(board, "cop")
    assert action["type"] == "move"
    dr, dc = {"S": (1, 0), "E": (0, 1), "SE": (1, 1)}.get(action["direction"], (None, None))
    assert dr is not None, f"expected a distance-closing direction, got {action}"
    new_pos = (board.cop_pos[0] + dr, board.cop_pos[1] + dc)
    assert manhattan_distance(new_pos, board.thief_pos) < manhattan_distance(board.cop_pos, board.thief_pos)


def test_thief_policy_moves_away_from_cop():
    board = Board((5, 5), max_barriers=0)
    board.set_start_positions(cop_pos=(2, 2), thief_pos=(2, 3))
    action = heuristic_policy(board, "thief")
    assert action["type"] == "move"
    from src.engine.board import DIRECTIONS
    dr, dc = DIRECTIONS[action["direction"]]
    new_pos = (board.thief_pos[0] + dr, board.thief_pos[1] + dc)
    assert manhattan_distance(new_pos, board.cop_pos) > manhattan_distance(board.thief_pos, board.cop_pos)


def test_cop_places_barrier_when_adjacent_and_barriers_remain():
    board = Board((5, 5), max_barriers=5)
    board.set_start_positions(cop_pos=(2, 2), thief_pos=(2, 3))
    # Cop is adjacent (distance 1) but a capturing move ("E") is also legal,
    # so the engine would still accept a barrier as the heuristic's pick.
    action = heuristic_policy(board, "cop")
    assert action == {"type": "place_barrier"}


def test_cop_does_not_barricade_with_no_barriers_remaining():
    board = Board((5, 5), max_barriers=0)
    board.set_start_positions(cop_pos=(2, 2), thief_pos=(2, 3))
    action = heuristic_policy(board, "cop")
    assert action["type"] == "move"


def test_candidate_actions_lists_every_direction_exactly_once():
    board = Board((5, 5), max_barriers=0)
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(4, 4))
    actions = heuristic_candidate_actions("cop", board, barriers_remaining=0, rng=random.Random(1))
    directions = [a["direction"] for a in actions if a["type"] == "move"]
    assert sorted(directions) == sorted(["N", "S", "E", "W", "NE", "NW", "SE", "SW"])


def test_thief_picks_a_random_direction_when_opponent_unknown_not_a_fixed_one():
    board = Board((5, 5), max_barriers=0)
    board.set_start_positions(cop_pos=(2, 2), thief_pos=(2, 3))
    board.cop_pos = UNKNOWN_POSITION  # simulates make_belief_board's "no estimate" case
    picks = set()
    for seed in range(20):
        actions = heuristic_candidate_actions("thief", board, barriers_remaining=0, rng=random.Random(seed))
        picks.add(actions[0]["direction"])
    # Not locked onto one or two directions every time, unlike the old
    # fixed-grid-center-default behavior this replaces.
    assert len(picks) > 2


def test_cop_does_not_barricade_on_unknown_opponent():
    board = Board((5, 5), max_barriers=5)
    board.set_start_positions(cop_pos=(2, 2), thief_pos=(2, 3))
    board.thief_pos = UNKNOWN_POSITION
    action = heuristic_policy(board, "cop")
    assert action != {"type": "place_barrier"}


def test_candidate_actions_best_pick_is_distance_closing_for_cop():
    board = Board((5, 5), max_barriers=0)
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(4, 4))
    actions = heuristic_candidate_actions("cop", board, barriers_remaining=0, rng=random.Random(1))
    best = actions[0]
    from src.engine.board import DIRECTIONS
    dr, dc = DIRECTIONS[best["direction"]]
    new_pos = (board.cop_pos[0] + dr, board.cop_pos[1] + dc)
    assert manhattan_distance(new_pos, board.thief_pos) <= manhattan_distance(board.cop_pos, board.thief_pos)
