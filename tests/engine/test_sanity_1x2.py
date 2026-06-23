"""1x2 sanity check (per the plan's gradual-sanity-check progression):
confirms win conditions, barrier logic, and scoring all work correctly on
the smallest possible board before scaling up to larger grids.
"""

from src.engine.board import Board
from src.engine.game import run_game_series
from src.engine.subgame import run_subgame

SCORING = {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5}


def test_1x2_capture_when_cop_steps_onto_thief():
    board = Board((1, 2), max_barriers=0)
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(0, 1))

    def thief_blocked(board, agent):
        return {"type": "move", "direction": "E"}  # out of bounds, rejected

    def cop_advances(board, agent):
        return {"type": "move", "direction": "E"}

    result = run_subgame(board, max_moves=5, thief_policy=thief_blocked, cop_policy=cop_advances)
    assert result["winner"] == "cop"
    assert result["moves_taken"] == 1


def test_1x2_thief_survives_when_cop_cannot_advance():
    board = Board((1, 2), max_barriers=0)
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(0, 1))

    def thief_blocked(board, agent):
        return {"type": "move", "direction": "E"}  # out of bounds, rejected

    def cop_blocked(board, agent):
        return {"type": "move", "direction": "W"}  # also out of bounds

    result = run_subgame(board, max_moves=4, thief_policy=thief_blocked, cop_policy=cop_blocked)
    assert result["winner"] == "thief"
    assert result["moves_taken"] == 4


def test_1x2_cop_barrier_on_own_cell_does_not_crash_no_legal_moves_left():
    board = Board((1, 2), max_barriers=1)
    board.set_start_positions(cop_pos=(0, 0), thief_pos=(0, 1))

    def thief_stays(board, agent):
        return {"type": "move", "direction": "E"}  # out of bounds on a 1x2 grid

    def cop_barricades_self(board, agent):
        return {"type": "place_barrier"}

    result = run_subgame(board, max_moves=3, thief_policy=thief_stays, cop_policy=cop_barricades_self)
    assert result["winner"] in ("cop", "thief")
    assert result["barriers_placed"] == 1


def test_1x2_full_series_scoring_totals_match_table(tmp_path):
    def thief_blocked(board, agent):
        return {"type": "move", "direction": "E"}  # out of bounds, rejected

    def cop_advances(board, agent):
        return {"type": "move", "direction": "E"}

    totals = run_game_series(
        grid_size=(1, 2),
        max_moves=5,
        num_games=6,
        max_barriers=0,
        scoring=SCORING,
        start_positions_fn=lambda grid: ((0, 0), (0, 1)),
        thief_policy=thief_blocked,
        cop_policy=cop_advances,
        results_dir=tmp_path,
    )
    assert totals["totals"]["cop"] == 6 * SCORING["cop_win"]
    assert totals["totals"]["thief"] == 6 * SCORING["thief_loss"]
