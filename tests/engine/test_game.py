"""Unit tests for the full game series: scoring accumulation across
multiple sub-games, matching the scoring table exactly."""

from src.engine.game import run_game_series

SCORING = {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5}


def fixed_start_positions(grid_size):
    return (0, 0), (0, grid_size[1] - 1)


def test_cop_always_wins_scores_match_table(tmp_path):
    def cop_chases_east(board, agent):
        return {"type": "move", "direction": "E"}

    def thief_stays(board, agent):
        return {"type": "move", "direction": "N"}  # always rejected

    totals = run_game_series(
        grid_size=(1, 3),
        max_moves=10,
        num_games=6,
        max_barriers=0,
        scoring=SCORING,
        start_positions_fn=fixed_start_positions,
        thief_policy=thief_stays,
        cop_policy=cop_chases_east,
        results_dir=tmp_path,
    )

    assert totals["totals"]["cop"] == 6 * SCORING["cop_win"]
    assert totals["totals"]["thief"] == 6 * SCORING["thief_loss"]
    assert len(totals["sub_games"]) == 6


def test_thief_always_survives_scores_match_table(tmp_path):
    def cop_stays(board, agent):
        return {"type": "move", "direction": "N"}  # always rejected

    def thief_stays(board, agent):
        return {"type": "move", "direction": "N"}

    totals = run_game_series(
        grid_size=(1, 3),
        max_moves=5,
        num_games=6,
        max_barriers=0,
        scoring=SCORING,
        start_positions_fn=fixed_start_positions,
        thief_policy=thief_stays,
        cop_policy=cop_stays,
        results_dir=tmp_path,
    )

    assert totals["totals"]["cop"] == 6 * SCORING["cop_loss"]
    assert totals["totals"]["thief"] == 6 * SCORING["thief_win"]
