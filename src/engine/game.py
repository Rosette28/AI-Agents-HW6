"""Full game series: runs num_games sub-games back to back, accumulates
scores per the scoring table, and persists each raw sub-game result.
"""

from src.engine.board import Board
from src.engine.results import save_subgame_result
from src.engine.subgame import run_subgame


def _score_subgame(winner: str, scoring: dict) -> tuple[int, int]:
    """Return (cop_points, thief_points) for one sub-game's outcome."""
    if winner == "cop":
        return scoring["cop_win"], scoring["thief_loss"]
    return scoring["cop_loss"], scoring["thief_win"]


def run_game_series(
    grid_size: tuple[int, int],
    max_moves: int,
    num_games: int,
    max_barriers: int,
    scoring: dict,
    start_positions_fn,
    thief_policy,
    cop_policy,
    results_dir=None,
) -> dict:
    """Run a full series of `num_games` sub-games and return totals.

    `start_positions_fn(grid_size) -> (cop_pos, thief_pos)` generates the
    starting positions for each sub-game (random or fixed, caller's choice).
    """
    cop_total = 0
    thief_total = 0
    subgame_results = []

    for index in range(1, num_games + 1):
        board = Board(grid_size, max_barriers)
        cop_pos, thief_pos = start_positions_fn(grid_size)
        board.set_start_positions(cop_pos, thief_pos)

        result = run_subgame(board, max_moves, thief_policy, cop_policy)
        cop_points, thief_points = _score_subgame(result["winner"], scoring)
        result["cop_points"] = cop_points
        result["thief_points"] = thief_points
        cop_total += cop_points
        thief_total += thief_points

        save_subgame_result(result, grid_size, index, results_dir)
        subgame_results.append(result)

    return {
        "totals": {"cop": cop_total, "thief": thief_total},
        "sub_games": subgame_results,
    }
