"""Pipeline sanity checks: a dummy message end to end on the 1x2 grid, then
a full sub-game and a full 6-sub-game series driven entirely through the
documented MCP tool contract (src/agents/orchestrator.py).
"""

import asyncio
import random

from src.agents.orchestrator import run_series_via_mcp, run_subgame_via_mcp


def test_dummy_message_travels_end_to_end_on_1x2_grid():
    """Client -> tool call -> MCP server -> response, logged on the session."""
    result = asyncio.run(
        run_subgame_via_mcp((1, 2), max_moves=25, max_barriers=5, cop_pos=(0, 0), thief_pos=(0, 1), rng=random.Random(7))
    )
    assert result["winner"] in {"cop", "thief"}
    assert result["transcript"], "expected at least one logged turn"
    first_turn = result["transcript"][0]
    assert first_turn["agent"] == "thief"
    assert "result" in first_turn


def test_full_subgame_terminates_with_a_winner():
    result = asyncio.run(
        run_subgame_via_mcp((3, 3), max_moves=25, max_barriers=5, cop_pos=(0, 0), thief_pos=(2, 2), rng=random.Random(3))
    )
    assert result["winner"] in {"cop", "thief"}
    assert 1 <= result["moves_taken"] <= 25


SCORING = {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5}


def _fixed_start_positions(grid_size):
    return (0, 0), (grid_size[0] - 1, grid_size[1] - 1)


def test_full_series_totals_match_scoring_table():
    series = asyncio.run(
        run_series_via_mcp((3, 3), max_moves=25, num_games=6, max_barriers=5,
                            scoring=SCORING, start_positions_fn=_fixed_start_positions, seed=11)
    )
    assert len(series["sub_games"]) == 6

    expected_cop = sum(g["cop_points"] for g in series["sub_games"])
    expected_thief = sum(g["thief_points"] for g in series["sub_games"])
    assert series["totals"] == {"cop": expected_cop, "thief": expected_thief}

    for game in series["sub_games"]:
        if game["winner"] == "cop":
            assert (game["cop_points"], game["thief_points"]) == (SCORING["cop_win"], SCORING["thief_loss"])
        else:
            assert (game["cop_points"], game["thief_points"]) == (SCORING["cop_loss"], SCORING["thief_win"])
