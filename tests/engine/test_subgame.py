"""Unit tests for the sub-game turn loop: capture and survival outcomes."""

from src.engine.board import Board
from src.engine.subgame import run_subgame


def stay_still_thief(board, agent):
    """Thief that never moves successfully (always tries an out-of-bounds
    direction so it's rejected and the position is unchanged)."""
    return {"type": "move", "direction": "N"}


def chase_cop(board, agent):
    """Cop that always steps East, ignoring the Thief — just to drive a
    deterministic, short capture scenario in tests."""
    return {"type": "move", "direction": "E"}


def test_capture_ends_subgame_with_cop_winner():
    board = Board((1, 3), max_barriers=0)
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(0, 2))

    def thief_noop(board, agent):
        return {"type": "move", "direction": "N"}  # always out of bounds

    result = run_subgame(board, max_moves=10, thief_policy=thief_noop, cop_policy=chase_cop)
    assert result["winner"] == "cop"
    assert result["final_cop_pos"] == result["final_thief_pos"]


def test_survival_to_max_moves_gives_thief_winner():
    board = Board((1, 5), max_barriers=0)
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(0, 4))

    def thief_noop(board, agent):
        return {"type": "move", "direction": "N"}  # out of bounds, never moves

    def cop_noop(board, agent):
        return {"type": "move", "direction": "S"}  # out of bounds, never moves

    result = run_subgame(board, max_moves=5, thief_policy=thief_noop, cop_policy=cop_noop)
    assert result["winner"] == "thief"
    assert result["moves_taken"] == 5


def test_thief_with_no_legal_moves_is_skipped_not_crashed():
    board = Board((1, 2), max_barriers=1)
    board.set_start_positions(cop_pos=(0, 1), thief_pos=(0, 0))
    board.barriers.add((0, 1))  # wall off Thief's only neighbor in advance

    def cop_stays(board, agent):
        return {"type": "place_barrier"}

    def thief_any(board, agent):
        return {"type": "move", "direction": "E"}

    result = run_subgame(board, max_moves=3, thief_policy=thief_any, cop_policy=cop_stays)
    assert result["winner"] in ("cop", "thief")
