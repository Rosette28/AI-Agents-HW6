"""Unit tests for Board: movement validation, barrier blocking, capture."""

import pytest

from src.engine.board import Board


def make_board(grid_size=(5, 5), max_barriers=5):
    return Board(grid_size, max_barriers)


def test_legal_move_updates_position():
    board = make_board()
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(4, 4))
    result = board.move("cop", "E")
    assert result["accepted"] is True
    assert board.cop_pos == (0, 1)


def test_move_out_of_bounds_rejected():
    board = make_board()
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(4, 4))
    result = board.move("cop", "N")
    assert result["accepted"] is False
    assert result["reason"] == "out_of_bounds"
    assert board.cop_pos == (0, 0)


def test_diagonal_move():
    board = make_board()
    board.set_start_positions(cop_pos=(2, 2), thief_pos=(0, 0))
    result = board.move("cop", "SE")
    assert result["accepted"] is True
    assert board.cop_pos == (3, 3)


def test_barrier_blocks_thief_and_cop():
    board = make_board()
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(4, 4))
    board.place_barrier()  # barricades (0, 0)
    board.cop_pos = (0, 1)
    result_cop = board.move("cop", "W")
    assert result_cop["accepted"] is False
    assert result_cop["reason"] == "blocked_by_barrier"

    board.thief_pos = (1, 0)
    result_thief = board.move("thief", "N")
    assert result_thief["accepted"] is False
    assert result_thief["reason"] == "blocked_by_barrier"


def test_barrier_cap_enforced():
    board = make_board(max_barriers=1)
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(4, 4))
    first = board.place_barrier()
    assert first["accepted"] is True
    board.cop_pos = (1, 1)
    second = board.place_barrier()
    assert second["accepted"] is False
    assert second["reason"] == "no_barriers_remaining"


def test_capture_detection():
    board = make_board()
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(0, 1))
    result = board.move("cop", "E")
    assert result["captured"] is True
    assert board.is_captured() is True


def test_same_start_position_rejected():
    board = make_board()
    with pytest.raises(ValueError):
        board.set_start_positions(cop_pos=(1, 1), thief_pos=(1, 1))


def test_legal_moves_excludes_barriers_and_out_of_bounds():
    board = make_board(grid_size=(1, 2))
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(0, 1))
    assert board.legal_moves((0, 0)) == ["E"]
